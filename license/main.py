import shutil
import subprocess
from datetime import datetime

import httpx
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

from crud import create_license, transliterate_license_filename
from dto.license_dto import LicensesInfo

from models import engine, Licenses, Base

app = FastAPI(title="LicenseService")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://auth:8030/token",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


def add_license_in_db(db, lic, machine_digest_file_name, lic_file_name):
    license = create_license(lic, machine_digest_file_name, lic_file_name)
    db.add(license)
    db.commit()
    db.refresh(license)


def save_machine_digest_file(machine_digest_file, machine_digest_file_name):
    path = f"license/files/machine_digest_files/{machine_digest_file_name}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)


def run_script_to_save_files(lic, machine_digest_file_name, lic_file_name):
    subprocess.run(
        [
            "python",
            "license/script.py",
            f"{lic.company_name}",
            f"{lic.product_name}",
            f"{lic.license_users_count}",
            f"{lic.exp_time}",
            f"{machine_digest_file_name}",
            f"{lic_file_name}",
        ],
    )


@app.post("/generate_license")
def generate_license(
    current_user: dict = Depends(get_current_user),
    lic: LicensesInfo = Depends(LicensesInfo.as_form),
    machine_digest_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    today_date = datetime.now().strftime("%Y-%m-%d")
    lic_file_name = (
        transliterate_license_filename(
            lic.company_name, lic.product_name, lic.license_users_count
        )
        + f"_{lic.exp_time}"
    )
    machine_digest_file_name = (
        transliterate_license_filename(
            lic.company_name, lic.product_name, lic.license_users_count
        )
        + f"_{today_date}"
    )

    add_license_in_db(db, lic, machine_digest_file_name, lic_file_name)
    save_machine_digest_file(machine_digest_file, machine_digest_file_name)
    run_script_to_save_files(lic, machine_digest_file_name, lic_file_name)

    license_path = f"license/files/licenses/{lic_file_name}.txt"
    logger.bind(lic_file_name=lic_file_name, user=current_user).info("Создана лицензия")

    return FileResponse(license_path, filename=f"{lic_file_name}.txt")


@app.get("/all_licenses")
def get_all_licenses(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    all_licenses = db.query(Licenses).all()
    _logger = logger.bind(user=current_user)

    if not all_licenses:
        _logger.info("Выведен пустой список лицензий")
        return {
            "status": "success",
            "all_licenses": [],
        }

    _logger.info("Выведен список всех лицензий")
    return {
        "status": "success",
        "all_licenses": all_licenses,
    }


@app.get("/license/{id}")
def find_license(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id, user=current_user)

    if license is not None:
        license_path = f"license/files/licenses/{license.lic_file_name}"
        _logger.info(f"Выведена информация о лицензии с id: {id}")
        return FileResponse(license_path, filename=f"{license.lic_file_name}")
    else:
        _logger.error(f"Попытка найти информацию о несуществующей лицензии с id: {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензия с id-{id} не найдена",
        )


@app.get("/machine_digest_file/{id}")
def find_machine_digest(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id, user=current_user)
    digest_path = f"license/files/machine_digest_files/{license.machine_digest_file}"

    if license is not None:
        _logger.info("Выведена информацию о машинном файле с id")
        return FileResponse(digest_path, filename=f"{license.lic_file_name}")
    else:
        _logger.error(f"Попытка найти информацию о несуществующем машинном файле с id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензия с id-{id} не найдена",
        )


app.mount(
    "/license/files/licenses",
    StaticFiles(directory="files/licenses"),
    name="licenses")

app.mount(
    "/machine_digest_files",
    StaticFiles(directory="files/machine_digest_files"),
    name="machine_digest_files")

logger.add(
    "license/logs/log.log",
    level="INFO",
    format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message}  ||  {extra}",
    rotation="09:00",
    compression="zip",
    colorize=None,
)
