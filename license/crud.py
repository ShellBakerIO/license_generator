import json
import re
import shutil
from datetime import datetime

import transliterate
from fastapi import HTTPException

from models import Licenses


def transliterate_license_filename(company_name, product_name, license_users_count):
    russian_letter = f"{company_name}_{product_name}_{license_users_count}"
    english_letter = transliterate.translit(russian_letter, "ru", reversed=True)

    return english_letter


def create_license(lic, machine_digest_file_name, lic_file_name):
    pattern = r"^\d{4}[-./ ](0[1-9]|1[0-2])[-./ ](0[1-9]|[12][0-9]|3[01])$"
    print("DATE", lic.exp_time)
    match = re.fullmatch(pattern, lic.exp_time)
    if match is None:
        raise HTTPException(status_code=422, detail="Invalid license date format. Correct format is YYYY-MM-DD")
    else:
        lic.exp_time = datetime.strptime(f"{match[0]}", "%Y-%m-%d")

        license = Licenses(
            company_name=lic.company_name,
            product_name=lic.product_name,
            license_users_count=lic.license_users_count,
            exp_time=lic.exp_time,
            additional_license_information=lic.additional_license_information,
            machine_digest_file=machine_digest_file_name,
            lic_file_name=f"{lic_file_name}.txt",
        )
    return license


def form_file_name(lic):
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
    return lic_file_name, machine_digest_file_name


def add_license_in_db(db, lic, machine_digest_file_name, lic_file_name):
    license = create_license(lic, machine_digest_file_name, lic_file_name)
    db.add(license)
    db.commit()
    db.refresh(license)


def save_machine_digest_file(machine_digest_file, machine_digest_file_name):
    path = f"files/machine_digest_files/{machine_digest_file_name}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)


def save_license_file(lic, license_path, machine_digest_file_name,):
    path = f"files/machine_digest_files/{machine_digest_file_name}"
    product_key = open(path, "r", encoding="utf-8").read()

    license_data = {
        "company": lic.company_name,
        "product_name": lic.product_name,
        "license_users_count": lic.license_users_count,
        "exp_time": str(lic.exp_time),
        "product_key": product_key,
    }

    if lic.additional_license_information:
        additional_license_information = json.loads(lic.additional_license_information)
        additional_info = {}
        for key in additional_license_information:
            additional_info[key] = additional_license_information[key]
        license_data["additional_info"] = additional_info

    with open(license_path, "w", encoding="utf-8") as f:
        json.dump(license_data, f, ensure_ascii=False, indent=4)
