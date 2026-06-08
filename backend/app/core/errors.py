from typing import Any, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError


HTTP_STATUS_BY_CODE = {
    40001: 400,
    40002: 400,
    40101: 401,
    40301: 403,
    40401: 404,
    40901: 409,
    40902: 409,
    50000: 500,
}


class AppError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Any] = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    @property
    def http_status(self) -> int:
        return HTTP_STATUS_BY_CODE.get(self.code, 500)


def not_found(resource: str) -> AppError:
    return AppError(40401, "%s不存在" % resource)


def conflict(message: str) -> AppError:
    return AppError(40901, message)


def bad_business_value(message: str) -> AppError:
    return AppError(40002, message)


def translate_db_error(exc: SQLAlchemyError) -> AppError:
    message = str(getattr(exc, "orig", exc))
    if isinstance(exc, IntegrityError):
        if "Duplicate entry" in message or "UNIQUE" in message:
            return AppError(40902, "唯一约束冲突")
        return AppError(40901, message)

    if any(token in message for token in ("不存在", "not found", "NOT FOUND")):
        return AppError(40401, message)
    if any(token in message for token in ("重复", "Duplicate entry", "唯一")):
        return AppError(40902, message)
    if any(
        token in message
        for token in (
            "不是空闲",
            "不能",
            "只有",
            "状态",
            "已结束",
            "未启用",
            "重复",
        )
    ):
        return AppError(40901, message)
    if any(token in message for token in ("时间", "人数", "金额", "非法")):
        return AppError(40002, message)
    return AppError(50000, "数据库操作失败")
