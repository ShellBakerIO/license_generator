import re
from datetime import datetime

from models import Licenses
import transliterate


def transliterate_license_filename(company_name, product_name, license_users_count):
    russian_letter = f"{company_name}_{product_name}_{license_users_count}"
    english_letter = transliterate.translit(russian_letter, 'ru', reversed=True)

    return english_letter


def create_license(lic, machine_digest_file_name, lic_file_name):
    pattern = r"(\d{2})[^0-9]?(\d{2})[^0-9]?(\d{4})"
    match = re.fullmatch(pattern, lic.exp_time)

    license = Licenses(company_name=lic.company_name,
                       product_name=lic.product_name,
                       license_users_count=lic.license_users_count,
                       exp_time=datetime.strptime(f"{match[3]}-{match[2]}-{match[1]}", "%Y-%m-%d"),
                       machine_digest_file=machine_digest_file_name,
                       lic_file_name=f"{lic_file_name}.txt")
    return license
