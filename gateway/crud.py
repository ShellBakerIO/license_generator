from aiohttp.formdata import FormData


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
