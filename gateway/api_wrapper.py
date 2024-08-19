from functools import wraps
from typing import Any, Optional, Union

import aiohttp
from fastapi import Request, Response
from fastapi.routing import APIRouter
from aiohttp.formdata import FormData

router = APIRouter()


def gateway_router(method, path: str, payload_key: str, service_url: str, response_model: Optional[Any] = None):
    app_method = method(path, response_model=response_model)

    def wrapper(endpoint):
        @app_method
        @wraps(endpoint)
        async def decorator(request: Request, response: Response, **kwargs):
            scope = request.scope
            headers = {}
            request_method = scope['method'].lower()
            path = scope['path']
            payload = kwargs.get(payload_key)

            print(1, kwargs)
            print(2, payload)
            print(3, payload_key)

            if payload_key == 'form_data':
                data = FormData()
                data.add_field('username', payload.username)
                data.add_field('password', payload.password)
            else:
                data = payload.__dict__ if payload else {}

            print(4, data)

            url = f'{service_url}{path}'

            response_data = await send_request(
                url=url,
                method=request_method,
                data=data,
                headers=headers
            )

            return response_data

        return decorator

    return wrapper


async def send_request(url: str, method: str, data: Union[dict, FormData], headers: dict = None):
    if headers is None:
        headers = {}

    async with aiohttp.ClientSession() as session:
        request = getattr(session, method)

        if isinstance(data, dict):
            async with request(url=url, json=data, headers=headers) as response:
                print(5, data)
                data = await response.json()
        else:
            async with request(url=url, data=data, headers=headers) as response:
                print(6, data)
                data = await response.json()

        return data
