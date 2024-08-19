from aiohttp.formdata import FormData
from fastapi.responses import FileResponse


def generate_data(kwargs, payload, payload_key):
    data = {}

    if payload_key == 'form_data':
        data = FormData()
        data.add_field('username', payload.username)
        data.add_field('password', payload.password)
    elif payload_key == 'generate_license':
        data = FormData()
        lic = kwargs['lic']
        machine_digest_file = kwargs['machine_digest_file']

        data.add_field('company_name', lic.company_name)
        data.add_field('product_name', lic.product_name)
        data.add_field('license_users_count', str(lic.license_users_count))
        data.add_field('exp_time', lic.exp_time)
        data.add_field('machine_digest_file', machine_digest_file.file,
                       filename=machine_digest_file.filename,
                       content_type=machine_digest_file.content_type)
    else:
        data = payload.__dict__ if payload else {}

    return data


async def extract_response_data(response):
    content_type = response.headers.get('Content-Type', '')
    if 'application/json' in content_type:
        data = await response.json()
    elif 'text/plain' in content_type or 'application/octet-stream' in content_type:
        file_name = response.headers.get('Content-Disposition').split("filename=")[1].strip('"')
        file_content = await response.read()

        temp_file_path = f'/tmp/{file_name}'
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)

        return FileResponse(path=temp_file_path, filename=file_name)
    else:
        data = await response.read()

    return data
