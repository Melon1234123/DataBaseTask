from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_access_token, verify_password
from app.repositories.hotel_repository import HotelRepository


class AuthService:
    def __init__(self, repo: HotelRepository) -> None:
        self.repo = repo

    def login(self, account_name: str, password: str) -> dict:
        account = self.repo.get_account_by_name(account_name)
        if account is None or not verify_password(password, account["passwordHash"]):
            raise AppError(40101, "账号名或密码错误")
        if account["approvalStatus"] != "已启用":
            raise AppError(40301, "账号未启用，不能登录")

        settings = get_settings()
        token = create_access_token(
            str(account["accountId"]),
            {
                "accountName": account["accountName"],
                "permissionName": account["permissionName"],
            },
        )
        return {
            "accessToken": token,
            "tokenType": "Bearer",
            "expiresIn": settings.access_token_expire_seconds,
            "account": {
                "accountId": account["accountId"],
                "accountName": account["accountName"],
                "permissionName": account["permissionName"],
                "approvalStatus": account["approvalStatus"],
            },
        }
