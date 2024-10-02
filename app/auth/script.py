import sys


company_name = sys.argv[1]
product_name = sys.argv[2]
lic_num = sys.argv[3]
exp_time = sys.argv[4]
machine_digest_file_name = sys.argv[5]
lic_file_name = sys.argv[6]

path = f"app/files/machine_digest_files/{machine_digest_file_name}"
product_key = open(path, "r", encoding="utf-8").read()

license_path = f"app/files/licenses/{lic_file_name}.txt"
with open(license_path, "w", encoding="utf-8") as f:
    f.write("Компания: {}\n".format(company_name))
    f.write("ПО: {}\n".format(product_name))
    f.write("Количество лицензий: {}\n".format(lic_num))
    f.write("Время действия: {}\n".format(exp_time))
    f.write("Ключ продукта: {}\n".format(product_key))
