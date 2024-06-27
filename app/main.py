from fastapi import FastAPI, UploadFile, Form, File, Depends
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker
from app.auth.crud import create_license, overwriting_file
from app.auth.models import engine, Licenses, Base


class LicensesInfo(BaseModel):
    company_name: str
    product_name: str
    lic_num: int
    exp_time: str
    lic_file_name: str

    @classmethod
    def as_form(cls, company_name: str = Form(...), product_name: str = Form(...),
                lic_num: int = Form(...), exp_time: str = Form(...), lic_file_name: str = Form(...)):

        return cls(company_name=company_name,
                   product_name=product_name,
                   lic_num=lic_num,
                   exp_time=exp_time,
                   lic_file_name=lic_file_name)


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


@app.post("/generate_license")
def generate_license(lic: LicensesInfo = Depends(LicensesInfo.as_form), machine_digest_file: UploadFile = File(...), db: Session = Depends(get_db)):
    if machine_digest_file.content_type != "text/plain":
        return {
            "status": "error",
            "message": "Content-type must be text/plain"
        }

    license = create_license(lic, machine_digest_file)
    db.add(license)
    db.commit()
    db.refresh(license)

    new_license = overwriting_file(machine_digest_file, lic.lic_file_name)

    return {
        "status": "success",
        "message": f"Лицензия {new_license.name} создана",
    }


@app.get("/all_licenses")
def get_all_licenses(db: Session = Depends(get_db)):
    all_licenses = db.query(Licenses).all()

    if not all_licenses:
        return {
            "status": "error",
            "all_licenses": "Список лицензий пуст"
        }
    return {
        "status": "success",
        "all_licenses": all_licenses
    }


@app.get("/license/{id}")
def find_license(id: int, db: Session = Depends(get_db)):

    license = db.get(Licenses, id)

    if license is not None:
        return {
            "status": "success",
            "message": license
        }
    else:
        return {
            "status": "error",
            "message": f"Лицензия с id-{id} не найдена"
        }


@app.delete("/delete_license")
def delete_license(id: int, db: Session = Depends(get_db)):
    try:
        license = db.get(Licenses, id)
        deleted_file_name = license.lic_file_name
        db.delete(license)
        db.commit()

        os.remove(f"C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses/{deleted_file_name}")

        return {
            "status": "success",
            "message": f"Лицензия id-{id} name-{deleted_file_name} удалена",
            "license": license,
        }
    except Exception:
        return {
            "status": "error",
            "message": None
        }


app.mount("/licenses", StaticFiles(directory="C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses"), name="licenses")
app.mount("/machine_digest_files", StaticFiles(directory="C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/machine_digest_files"), name="machine_digest_files")
