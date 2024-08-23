import os
from functools import wraps
from typing import Any, Optional, Union

import aiohttp
import jwt
from aiohttp.formdata import FormData
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

import crud

router = APIRouter()


def gateway_router(method,
                   path: str,
                   payload_key: str,
                   service_url: str,
                   access_level: str | None = None,
                   response_model: Optional[Any] = None):
    app_method = method(path, response_model=response_model)

    def wrapper(endpoint):
        @app_method
        @wraps(endpoint)
        async def decorator(request: Request, response: Response, **kwargs):
            if access_level is None:
                scope = request.scope
                headers = {}
                request_method = scope['method'].lower()
                path = scope['path']
                payload = kwargs.get(payload_key)
                data = crud.form_data(kwargs, payload, payload_key)
                url = crud.form_url(service_url, path, kwargs)

                response_data = await send_request(
                    url=url,
                    method=request_method,
                    data=data,
                    headers=headers
                )

                return response_data
            else:
                try:
                    decoded_token = jwt.decode(kwargs.get('token'),
                                               os.getenv("SECRET_KEY"),
                                               algorithms=['HS256'],
                                               options={'verify_aud': True}
                                               )
                    has_access = decoded_token["claims"]

                    if access_level in has_access:
                        scope = request.scope
                        headers = {}
                        request_method = scope['method'].lower()
                        path = scope['path']
                        payload = kwargs.get(payload_key)
                        data = crud.form_data(kwargs, payload, payload_key)
                        url = crud.form_url(service_url, path, kwargs)

                        response_data = await send_request(
                            url=url,
                            method=request_method,
                            data=data,
                            headers=headers
                        )

                        return response_data
                    else:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
                except jwt.InvalidSignatureError or jwt.DecodeError:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return wrapper


async def send_request(url: str, method: str, data: Union[dict, FormData], headers: dict = None):
    if headers is None:
        headers = {}

    async with aiohttp.ClientSession() as session:
        request = getattr(session, method)
        if isinstance(data, dict):
            async with request(url=url, json=data, headers=headers) as response:
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
        else:
            async with request(url=url, data=data, headers=headers) as response:
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
