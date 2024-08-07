from functools import wraps
from typing import Any, Optional, Tuple

from fastapi import HTTPException, Request, Response, status
from fastapi.routing import APIRouter
import httpx

router = APIRouter()


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

        return decorator

    return wrapper


async def send_request(request: Request) -> Tuple[Any, int]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=str(request.url),
                headers=dict(request.headers),
                json=await request.json() if request.method in ["POST", "PUT", "PATCH"] else None,
                params=request.query_params if request.method == "GET" else None
            )
        return response.json(), response.status_code
    except httpx.RequestError as e:
        return {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
