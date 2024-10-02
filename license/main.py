from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

import crud
from dto.license_dto import LicensesInfo
from models import engine, Licenses, Base

app = FastAPI(title="LicenseService")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/generate_license")
def generate_license(lic: LicensesInfo = Depends(LicensesInfo.as_form), machine_digest_file: UploadFile = File(...), db: Session = Depends(get_db)):
    if machine_digest_file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="File type not supported")

    try:
        lic_file_name, machine_digest_file_name = crud.form_file_name(lic)
        crud.add_license_in_db(db, lic, machine_digest_file_name, lic_file_name)
        crud.save_machine_digest_file(machine_digest_file, machine_digest_file_name)
        license_path = f"files/licenses/{lic_file_name}.txt"
        crud.save_license_file(lic, license_path, machine_digest_file_name)

        logger.bind(lic_file_name=lic_file_name).info("Создана лицензия")

        f = FileResponse(license_path, filename=f"{lic_file_name}.txt")
    except Exception as e:
        print(f"Error - {str(e)} - {e.with_traceback()}")
        raise HTTPException(status_code=1337,
                            detail=f"Error - {str(e)}")
    return f


@app.get("/all_licenses")
def get_all_licenses(db: Session = Depends(get_db)):
    all_licenses = db.query(Licenses).all()

    if not all_licenses:
        logger.info("Выведен пустой список лицензий")
        return {
            "all_licenses": [],
        }

    logger.info("Выведен список всех лицензий")
    return {
        "all_licenses": all_licenses,
    }


@app.get("/license/{license_id}")
def find_license(license_id: int, db: Session = Depends(get_db)):
    license_stmt = db.get(Licenses, license_id)
    _logger = logger.bind(id=license_id)

    if license_stmt is not None:
        license_path = f"files/licenses/{license_stmt.lic_file_name}"
        _logger.info("Выведена информация о лицензии с id")
        return FileResponse(license_path, filename=f"{license_stmt.lic_file_name}")
    else:
        _logger.error("Попытка найти информацию о несуществующей лицензии с id")
        raise HTTPException(status_code=404, detail=f"Лицензия с id-{license_id} не найдена")


@app.get("/machine_digest_file/{license_id}")
def find_machine_digest(license_id: int, db: Session = Depends(get_db)):
    license_client = db.get(Licenses, license_id)
    _logger = logger.bind(id=license_id)

    if license_client is not None:
        digest_path = f"files/machine_digest_files/{license_client.machine_digest_file}"
        _logger.info("Выведена информация о машинном файле с id")
        return FileResponse(digest_path, filename=f"{license_client.machine_digest_file}")
    else:
        _logger.error("Попытка найти информацию о несуществующем машинном файле с id")
        raise HTTPException(status_code=404, detail=f"Машинный файл с id-{license_id} не найден")


app.mount(
    "/licenses",
    StaticFiles(directory="files/licenses"),
    name="licenses",
)

app.mount(
    "/machine_digest_files",
    StaticFiles(directory="files/machine_digest_files"),
    name="machine_digest_files",
)

logger.add(
    "/license/logs/log.log",
    level="INFO",
    format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message}  ||  {extra}",
    rotation="09:00",
    compression="zip",
    colorize=None,
)
