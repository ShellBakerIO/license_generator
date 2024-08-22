import json
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
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
def generate_license(
        lic: LicensesInfo = Depends(LicensesInfo.as_form),
        machine_digest_file: UploadFile = File(...),
        db: Session = Depends(get_db),
):
    if machine_digest_file.content_type != "text/plain":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not supported")

    today_date = datetime.now().strftime("%Y-%m-%d")
    lic_file_name = (
            crud.transliterate_license_filename(lic.company_name, lic.product_name, lic.license_users_count)
            + f"_{lic.exp_time}"
    )
    machine_digest_file_name = (
            crud.transliterate_license_filename(lic.company_name, lic.product_name, lic.license_users_count)
            + f"_{today_date}"
    )

    crud.add_license_in_db(db, lic, machine_digest_file_name, lic_file_name)
    crud.save_machine_digest_file(machine_digest_file, machine_digest_file_name)

    path = f"files/machine_digest_files/{machine_digest_file_name}"
    product_key = open(path, "r", encoding="utf-8").read()

    license_data = {
        "company": lic.company_name,
        "product_name": lic.product_name,
        "license_users_count": lic.license_users_count,
        "exp_time": lic.exp_time,
        "product_key": product_key
    }

    license_path = f"files/licenses/{lic_file_name}.txt"
    with open(license_path, "w", encoding="utf-8") as f:
        json.dump(license_data, f, ensure_ascii=False, indent=4)

    logger.bind(lic_file_name=lic_file_name).info("Создана лицензия")

    return FileResponse(license_path, filename=f"{lic_file_name}.txt")


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


@app.get("/license/{id}")
def find_license(id: int, db: Session = Depends(get_db)):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id)

    if license is not None:
        license_path = f"files/licenses/{license.lic_file_name}"
        _logger.info("Выведена информация о лицензии с id")
        return FileResponse(license_path, filename=f"{license.lic_file_name}")
    else:
        _logger.error("Попытка найти информацию о несуществующей лицензии с id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензия с id-{id} не найдена",
        )


@app.get("/machine_digest_file/{id}")
def find_machine_digest(id: int, db: Session = Depends(get_db)):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id)

    if license is not None:
        digest_path = f"files/machine_digest_files/{license.machine_digest_file}"
        _logger.info("Выведена информация о машинном файле с id")
        return FileResponse(digest_path, filename=f"{license.machine_digest_file}")
    else:
        _logger.error("Попытка найти информацию о несуществующем машинном файле с id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Машинный файл с id-{id} не найден",
        )


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
