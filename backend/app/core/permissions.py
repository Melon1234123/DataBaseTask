from dataclasses import dataclass
from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.repositories.hotel_repository import HotelRepository


ROLE_ADMIN = "管理员"
ROLE_FRONT_DESK = "前台工作人员"
ROLE_CLEANER = "保洁员"
ROLE_AUDITOR = "审计员"

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AccountPrincipal:
    account_id: int
    account_name: str
    permission_id: int
    permission_name: str
    approval_status: str


def _principal_from_row(row: dict) -> AccountPrincipal:
    return AccountPrincipal(
        account_id=row["accountId"],
        account_name=row["accountName"],
        permission_id=row["permissionId"],
        permission_name=row["permissionName"],
        approval_status=row["approvalStatus"],
    )


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AccountPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(40101, "未登录或 token 无效")
    payload = decode_access_token(credentials.credentials)
    try:
        account_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise AppError(40101, "未登录或 token 无效")

    row = HotelRepository(db).get_account(account_id)
    if row is None or row["approvalStatus"] != "已启用":
        raise AppError(40101, "未登录或 token 无效")
    return _principal_from_row(row)


def require_roles(*roles: str) -> Callable:
    def dependency(
        current_account: AccountPrincipal = Depends(get_current_account),
    ) -> AccountPrincipal:
        if current_account.permission_name not in roles:
            raise AppError(40301, "当前角色无权限")
        return current_account

    return dependency
