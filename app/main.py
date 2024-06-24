from fastapi import FastAPI, UploadFile, Form, File, Depends
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth.crud import create_license, overwriting_file
from app.auth.models import engine, Licenses


app = FastAPI(tittle="LicenseGenerator")


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


@app.get("/licenses")
def get_all_licenses():
    try:
        with Session(autoflush=False, bind=engine) as db:
            all_licenses = db.query(Licenses).all()
        return {
            "status": "success",
            "all_licenses": all_licenses
        }
    except Exception:
        return {
            "status": "error"
        }


@app.get("/license/{id}")
def find_license(id: int):
    try:
        with Session(autoflush=False, bind=engine) as db:
            license = db.get(Licenses, id)
        return {
            "status": "success",
            "message": license
        }
    except Exception:
        return {
            "status": "error",
            "message": f"Лицензия с id-{id} не найдена"
        }


@app.post("/generate_license")
def generate_license(lic: LicensesInfo = Depends(LicensesInfo.as_form), machine_digest_file: UploadFile = File(...)):
    if machine_digest_file.content_type != "text/plain":
        return {
            "status": "error",
            "message": "Content-type must be text/plain"
        }

    with Session(bind=engine) as db:
        license = create_license(lic, machine_digest_file)
        db.add(license)
        db.commit()

    new_license = overwriting_file(machine_digest_file, lic.lic_file_name)

    return {
        "status": "success",
        "message": f"Лицензия {new_license.name} создана",
    }


@app.delete("/delete_license")
def delete_license(id: int):
    try:
        with Session(autoflush=False, bind=engine) as db:
            license = db.get(Licenses, id)
            deleted_file_name = license.lic_file_name
            db.delete(license)
            db.commit()

        os.remove(f"app/files/licenses/{deleted_file_name}")

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


app.mount("/app", StaticFiles(directory="app/files/machine_digest_files"), name="machine_digest_files")
app.mount("/app", StaticFiles(directory="app/files/licenses"), name="licenses")
