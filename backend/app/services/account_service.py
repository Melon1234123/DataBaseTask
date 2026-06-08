from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.core.security import hash_password
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def register(self, payload: dict) -> dict:
        password = payload.pop("password")
        with transactional(self.db):
            account_id = self.repo.create_account(payload, hash_password(password))
        return self.repo.get_account(account_id)

    def list_accounts(self, page: int, page_size: int, approval_status=None, permission_id=None):
        return self.repo.list_accounts(page, page_size, approval_status, permission_id)

    def get_account(self, account_id: int) -> dict:
        account = self.repo.get_account(account_id)
        if account is None:
            raise not_found("账号")
        return account

    def update_account(self, account_id: int, values: dict) -> dict:
        self.get_account(account_id)
        with transactional(self.db):
            self.repo.update_account(account_id, values)
        return self.get_account(account_id)

    def approve_account(self, account_id: int, approval_status: str) -> dict:
        self.get_account(account_id)
        if approval_status not in ("已启用", "已驳回", "已停用"):
            raise AppError(40002, "账号审批状态非法")
        with transactional(self.db):
            self.repo.approve_account(account_id, approval_status)
        return self.get_account(account_id)

    def list_permissions(self) -> list:
        return self.repo.list_permissions()
