from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import database_health
from app.core.errors import AppError, translate_db_error
from app.core.responses import error_response, new_request_id, success
from app.routers import accounts, audit, auth, checkins, checkouts, cleaning, customers, reservations, rooms


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id") or new_request_id()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return error_response(
        request,
        code=exc.code,
        message=exc.message,
        status_code=exc.http_status,
        data=exc.data,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": item.get("loc"), "msg": item.get("msg"), "type": item.get("type")}
        for item in exc.errors()
    ]
    return error_response(
        request,
        code=40001,
        message="参数格式错误或必填缺失",
        status_code=400,
        data=errors,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    translated = translate_db_error(exc)
    return error_response(
        request,
        code=translated.code,
        message=translated.message,
        status_code=translated.http_status,
        data=translated.data,
    )


@app.get("/health", tags=["system"])
def health(request: Request):
    return success(
        request,
        {
            "status": "ok",
            "service": settings.app_name,
            "database": database_health(),
        },
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(accounts.router, prefix=settings.api_v1_prefix)
app.include_router(customers.router, prefix=settings.api_v1_prefix)
app.include_router(rooms.router, prefix=settings.api_v1_prefix)
app.include_router(reservations.router, prefix=settings.api_v1_prefix)
app.include_router(checkins.router, prefix=settings.api_v1_prefix)
app.include_router(checkouts.router, prefix=settings.api_v1_prefix)
app.include_router(cleaning.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)

frontend_dir = Path(__file__).resolve().parents[2] / "hotel-frontend-minimal"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
