from functools import wraps
from typing import Any, Optional

from fastapi import HTTPException, Request, Response, status


def router(method, path: str, response_model: Optional[Any] = None):
    """
    Обёртка для валидации данных

    :param method: Вызываемый объект (функция) реализующая метод http-запроса.
    :param path: Адрес эндпоинта.
    :param response_model: Модель данных для преобразования ответа.
    """
    app_method = method(path, response_model=response_model)

    def wrapper(endpoint): # endpoint - base function
        @app_method
        @wraps(endpoint)
        async def decorator(request: Request, response: Response, **kwargs):
            response_data, response_status_code = await send_request(request)
            if int(response_status_code) >= status.HTTP_400_BAD_REQUEST:
                raise HTTPException(
                    status_code=response_status_code, detail=response_data
                )
            response.status_code = response_status_code
            return response_data

    return wrapper


async def send_request(request):
    return {"sorry", status.HTTP_501_NOT_IMPLEMENTED}
