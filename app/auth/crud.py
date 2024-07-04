from datetime import datetime
from app.auth.models import Licenses
import transliterate


def transliterate_license_filename(company_name, product_name, lic_num):
    russian_letter = f"{company_name}_{product_name}_{lic_num}"
    english_letter = transliterate.translit(russian_letter, 'ru', reversed=True)

    return english_letter


def create_license(lic, machine_digest_file_name, lic_file_name):
    license = Licenses(company_name=lic.company_name,
                       product_name=lic.product_name,
                       lic_num=lic.lic_num,
                       exp_time=datetime.strptime(lic.exp_time, "%d-%m-%Y").strftime("%d-%m-%Y"),
                       machine_digest_file=machine_digest_file_name,
                       lic_file_name=f"{lic_file_name}.txt")
    return license
