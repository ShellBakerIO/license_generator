import urllib.parse
from aiohttp.formdata import FormData
from fastapi import HTTPException


def form_data(kwargs, payload, payload_key):
    data = {}
    try:
        if payload_key == "form_data":
            data = FormData()
            data.add_field("username", payload.username)
            data.add_field("password", payload.password)
        elif payload_key == "generate_license":
            data = FormData()
            print(kwargs)
            lic = kwargs["lic"]
            machine_digest_file = kwargs["machine_digest_file"]

            data.add_field("company_name", lic.company_name)
            data.add_field("product_name", lic.product_name)
            data.add_field("license_users_count", str(lic.license_users_count))
            data.add_field("exp_time", lic.exp_time)
            data.add_field(
                "additional_license_information",
                lic.additional_license_information
            )
            data.add_field(
                "machine_digest_file",
                machine_digest_file.file,
                filename=machine_digest_file.filename,
                content_type=machine_digest_file.content_type,
            )

        elif payload_key == "id":
            data = {payload_key: payload}
        else:
            data = payload.__dict__ if payload else {}

        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def form_url(service_url: str, path: str, query_params: dict) -> str:
    url = f"{service_url}{path}"
    if query_params and path != "/token":
        del query_params["token"]
        query_string = urllib.parse.urlencode(query_params)
        url = f"{url}?{query_string}"

    return url
