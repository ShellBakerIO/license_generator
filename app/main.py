import os
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import FastAPI, UploadFile, Form, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, sessionmaker

from app.auth.crud import create_license, transliterate_license_filename, create_user
from app.auth.ldap import authenticate
from app.auth.models import engine, Licenses, Base, User


class LicensesInfo(BaseModel):
    company_name: str
    product_name: str
    license_users_count: int
    exp_time: str

    @classmethod
    def as_form(cls, company_name: str = Form(...), product_name: str = Form(...),
                license_users_count: int = Form(...), exp_time: str = Form(...)):

        return cls(company_name=company_name,
                   product_name=product_name,
                   license_users_count=license_users_count,
                   exp_time=exp_time)


app = FastAPI(tittle="LicenseGenerator")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'localhost:5173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"})

    decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithm="HS256")
    user = db.get(User, decoded_token["username"])

    if (user is not None) and (decoded_token["exp"] < datetime.utcnow()):
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"})


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    if not authenticate(form_data.username, form_data.password):
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.bind(user=form_data.username).info("В систему вошел пользователь")

    token_data = {
        "username": form_data.username,
        "exp": datetime.utcnow()+timedelta(seconds=960),
    }
    access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithm="HS256")

    user = create_user(form_data.username, access_token)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/users/me")
async def read_users_me(current_user: Annotated[Session, Depends(get_current_user)]):
    user = jwt.decode(current_user, os.getenv("SECRET_KEY"), algorithm="HS256")
    return user


def add_license_in_db(db, lic, machine_digest_file_name, lic_file_name):
    license = create_license(lic, machine_digest_file_name, lic_file_name)
    db.add(license)
    db.commit()
    db.refresh(license)


def save_machine_diggest_file(machine_digest_file, machine_digest_file_name):
    path = f"app/files/machine_digest_files/{machine_digest_file_name}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)


def run_script_to_save_files(lic, machine_digest_file_name, lic_file_name):
    subprocess.run(["python", "app/auth/script.py",
                    f"{lic.company_name}", f"{lic.product_name}", f"{lic.license_users_count}",
                    f"{lic.exp_time}", f"{machine_digest_file_name}", f"{lic_file_name}",], )


@app.post("/generate_license")
def generate_license(current_user: Annotated[Session, Depends(get_current_user)],
                     lic: LicensesInfo = Depends(LicensesInfo.as_form),
                     machine_digest_file: UploadFile = File(...),
                     db: Session = Depends(get_db)):

    today_date = datetime.now().strftime('%Y-%m-%d')
    lic_file_name = transliterate_license_filename(lic.company_name, lic.product_name, lic.license_users_count) + f"_{lic.exp_time}"
    machine_digest_file_name = transliterate_license_filename(lic.company_name, lic.product_name, lic.license_users_count) + f"_{today_date}"

    add_license_in_db(db, lic, machine_digest_file_name, lic_file_name)
    save_machine_diggest_file(machine_digest_file, machine_digest_file_name)
    run_script_to_save_files(lic, machine_digest_file_name, lic_file_name)

    license_path = f"app/files/licenses/{lic_file_name}.txt"
    logger.bind(lic_file_name=lic_file_name, user=current_user).info("Создана лицензия")

    return FileResponse(license_path, filename=f"{lic_file_name}.txt")


@app.get("/all_licenses")
def get_all_licenses(current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
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
def find_license(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id, user=current_user)

    if license is not None:
        license_path = f"app/files/licenses/{license.lic_file_name}"
        _logger.info(f"Выведена информацию о лицезии с id: {id}")
        return FileResponse(license_path, filename=f"{license.lic_file_name}")
    else:
        _logger.error(f"Попытка найти информацию о несуществующей лицензии с id: {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензия с id-{id} не найдена")


@app.get("/machine_digest_file/{id}")
def find_machine_digest(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    license = db.get(Licenses, id)
    _logger = logger.bind(id=id, user=current_user)
    digest_path = f"app/files/machine_digest_files/{license.machine_digest_file}"

    if license is not None:
        _logger.info("Выведена информацию о машинном файле с id")
        return FileResponse(digest_path, filename=f"{license.lic_file_name}")
    else:
        _logger.error(f"Попытка найти информацию о несуществующем машинном файле с id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензия с id-{id} не найдена")


def delete_license_in_db(db):
    license = db.get(Licenses, id)
    deleted_file_name = license.lic_file_name
    db.delete(license)
    db.commit()

    return deleted_file_name, license


@app.delete("/delete_license")
def delete_license(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    _logger = logger.bind(id=id, user=current_user)

    try:
        deleted_file_name, license = delete_license_in_db(db)
        os.remove(f"app/files/licenses/{deleted_file_name}")

        _logger.info("Удалена лицензия с id")
        return {
            "status": "success",
            "message": f"Лицензия id-{id} name-{deleted_file_name} удалена",
            "license": license,
        }

    except NoResultFound:
        _logger.error("Попытка удалить несуществующую лицензию с id")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лицензии с id-{id} не существует")


app.mount("/licenses",
          StaticFiles(directory="app/files/licenses"),
          name="licenses")
app.mount("/machine_digest_files",
          StaticFiles(directory="app/files/machine_digest_files"),
          name="machine_digest_files")

logger.add("app/logs/log.log",
           level="INFO",
           format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message}  ||  {extra}",
           rotation="09:00",
           compression="zip",
           colorize=None)
