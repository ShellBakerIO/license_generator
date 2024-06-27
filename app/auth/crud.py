import shutil
from datetime import datetime
from app.auth.models import Licenses


def overwriting_file(machine_digest_file, lic_file_name):
    path = f"C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/machine_digest_files/{machine_digest_file.filename}"
    with open(path, "wb+") as buffer:
        shutil.copyfileobj(machine_digest_file.file, buffer)

    new_file_info = open(path, "r", encoding="utf-8").readline()
    new_file_info = new_file_info[::-1]

    new_license = open(f"C:/Users/f.nasibov/PycharmProjects/fastApiProject1/app/files/licenses/{lic_file_name}.txt", mode='w')
    new_license.write(new_file_info)
    new_license.close()
    return new_license


def create_license(lic, machine_digest_file):
    license = Licenses(company_name=lic.company_name,
                       product_name=lic.product_name,
                       lic_num=lic.lic_num,
                       exp_time=datetime.strptime(lic.exp_time, "%d-%m-%Y"),
                       machine_digest_file=machine_digest_file.filename,
                       lic_file_name=f"{lic.lic_file_name}.txt")
    return license
