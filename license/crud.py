import re
import shutil
from datetime import datetime

import transliterate
from fastapi import HTTPException, status

from models import Licenses


def transliterate_license_filename(company_name, product_name, license_users_count):
    russian_letter = f"{company_name}_{product_name}_{license_users_count}"
    english_letter = transliterate.translit(russian_letter, 'ru', reversed=True)

    return english_letter


def create_license(lic, machine_digest_file_name, lic_file_name):
    pattern = r"^\d{4}[-./ ](0[1-9]|1[0-2])[-./ ](0[1-9]|[12][0-9]|3[01])$"
    print("DATE", lic.exp_time)
    match = re.fullmatch(pattern, lic.exp_time)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid license date format. Correct format is YYYY-MM-DD",
        )
    else:
        lic.exp_time = datetime.strptime(f"{match[0]}", "%Y-%m-%d")

        license = Licenses(company_name=lic.company_name,
                           product_name=lic.product_name,
                           license_users_count=lic.license_users_count,
                           exp_time=lic.exp_time,
                           machine_digest_file=machine_digest_file_name,
                           lic_file_name=f"{lic_file_name}.txt")
    return license


def add_license_in_db(db, lic, machine_digest_file_name, lic_file_name):
    license = create_license(lic, machine_digest_file_name, lic_file_name)
    db.add(license)
    db.commit()
    db.refresh(license)


def save_machine_digest_file(machine_digest_file, machine_digest_file_name):
    path = f"files/machine_digest_files/{machine_digest_file_name}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)
