from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def new_request_id() -> str:
    return "req-%s" % uuid4().hex


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", new_request_id())


def api_payload(
    request: Request,
    code: int = 0,
    message: str = "success",
    data: Optional[Any] = None,
) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
        "requestId": request_id(request),
    }


def success(request: Request, data: Optional[Any] = None, status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            api_payload(request=request, data=data),
            custom_encoder={Decimal: lambda value: format(value, "f")},
        ),
    )


def error_response(
    request: Request,
    code: int,
    message: str,
    status_code: int,
    data: Optional[Any] = None,
):
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            api_payload(request=request, code=code, message=message, data=data),
            custom_encoder={Decimal: lambda value: format(value, "f")},
        ),
    )
