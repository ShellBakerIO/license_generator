from functools import wraps
from typing import Any, Optional

import aiohttp
from fastapi import HTTPException, Request, Response, status
from fastapi.routing import APIRouter

import gateway_auth

router = APIRouter()


def gateway_router(method, path: str, payload_key: str, service_url: str, response_model: Optional[Any] = None):
    """
    Обёртка для валидации данных

    :param method: Вызываемый объект (функция) реализующая метод http-запроса.
    :param path: Адрес эндпоинта.
    :param payload_key:
    :param service_url: Адрес сервисса.
    :param response_model: Модель данных для преобразования ответа.
    """
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
            data = payload.__dict__ if payload else {}
            """if isinstance(kwargs, dict) and path != '/token':
                data = payload.__dict__ if payload else {}
            else:
                data = kwargs"""

            if path == '/token':
                headers = gateway_auth.login(form_data=data)

            url = f'{service_url}{path}'

            print(1, request_method)
            print(2, path)
            print(3, payload)
            print(4, data)
            print(5, headers)
            print(6, kwargs)
            print(7, url)

            response_data = await send_request(
                url=url,
                method=request_method,
                data=data,
                headers=headers
            )

            return response_data

    return wrapper


async def send_request(url: str, method: str, data: dict = None, headers: dict = None):
    if not data:
        data = {}

    async with aiohttp.ClientSession() as session:
        request = getattr(session, method)
        async with request(url=url, data=data, headers=headers) as response:
            print(data)
            print(url)
            print(data)
            data = await response.json()
            return data
