import os
import shutil
import subprocess
from datetime import datetime
from typing import Annotated
from loguru import logger

from fastapi import FastAPI, UploadFile, Form, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.auth.crud import create_license, transliterate_license_filename
from app.auth.ldap import get_user_info_by_username
from app.auth.models import engine, Licenses, Base


class LicensesInfo(BaseModel):
    company_name: str
    product_name: str
    lic_num: int
    exp_time: str

    @classmethod
    def as_form(cls, company_name: str = Form(...), product_name: str = Form(...),
                lic_num: int = Form(...), exp_time: str = Form(...)):

        return cls(company_name=company_name,
                   product_name=product_name,
                   lic_num=lic_num,
                   exp_time=exp_time)


app = FastAPI(tittle="LicenseGenerator")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = token
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"})

    return user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    if get_user_info_by_username(form_data.username, form_data.password) is False:
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему пользователя")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.bind(user=form_data.username).info("В систему вошел пользователь")
    return {
        "access_token": form_data.username,
        "token_type": "bearer"
    }


@app.get("/users/me")
async def read_users_me(current_user: Annotated[Session, Depends(get_current_user)]):
    return current_user


@app.post("/generate_license")
def generate_license(current_user: Annotated[Session, Depends(get_current_user)], lic: LicensesInfo = Depends(LicensesInfo.as_form),
                     machine_digest_file: UploadFile = File(...),
                     db: Session = Depends(get_db)):

    today_date = datetime.now().strftime('%d-%m-%Y')
    lic_file_name = transliterate_license_filename(lic.company_name, lic.product_name, lic.lic_num) + f"_{lic.exp_time}"
    machine_digest_file_name = transliterate_license_filename(lic.company_name, lic.product_name, lic.lic_num) + f"_{today_date}"

    license = create_license(lic, machine_digest_file_name, lic_file_name)
    db.add(license)
    db.commit()
    db.refresh(license)

    path = f"C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/machine_digest_files/{machine_digest_file_name}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)

    subprocess.run(["python", "C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/auth/script.py", f"{lic.company_name}", f"{lic.product_name}", f"{lic.lic_num}", f"{lic.exp_time}", f"{machine_digest_file_name}", f"{lic_file_name}",], )

    logger.bind(lic_file_name=lic_file_name, user=current_user).info(f"Создана лицензия")
    return {
        "status": "success",
        "message": f"Лицензия {lic_file_name} создана"
    }


@app.get("/all_licenses")
def get_all_licenses(current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    all_licenses = db.query(Licenses).all()
    shadow_logger = logger.bind(user=current_user)

    if not all_licenses:
        shadow_logger.error(f"Попытка вывести пустой список лицензий")
        return {
            "status": "error",
            "all_licenses": "Список лицензий пуст"
        }

    shadow_logger.info(f"Выведен список всех лицензий")
    return {
        "status": "success",
        "all_licenses": all_licenses
    }


@app.get("/license/{id}")
def find_license(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    license = db.get(Licenses, id)
    shadow_logger = logger.bind(id=id, user=current_user)

    if license is not None:
        shadow_logger.info(f"Выведена информацию о лицезии с id")
        return {
            "status": "success",
            "message": license
        }
    else:
        shadow_logger.error(f"Попытка удалить информацию о несуществующей лицензии с id")
        return {
            "status": "error",
            "message": f"Лицензия с id-{id} не найдена"
        }


@app.delete("/delete_license")
def delete_license(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
    shadow_logger = logger.bind(id=id, user=current_user)

    try:
        license = db.get(Licenses, id)
        deleted_file_name = license.lic_file_name
        db.delete(license)
        db.commit()

        os.remove(f"C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses/{deleted_file_name}")

        shadow_logger.info("Удалена лицензия с id")
        return {
            "status": "success",
            "message": f"Лицензия id-{id} name-{deleted_file_name} удалена",
            "license": license,
        }
    except Exception:
        shadow_logger.error("Введен несуществующий id")
        return {
            "status": "error",
            "message": None
        }


app.mount("/licenses", StaticFiles(directory="C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses"), name="licenses")
app.mount("/machine_digest_files", StaticFiles(directory="C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/machine_digest_files"), name="machine_digest_files")

logger.add("app/logs/log.log", level="INFO", format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message}  ||  {extra}", rotation="09:00", compression="zip", colorize=None)
