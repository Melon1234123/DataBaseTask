from datetime import date
from typing import Optional

from pydantic import Field

from app.schemas.common import CamelModel


class AccountRegisterRequest(CamelModel):
    account_name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)
    sex: Optional[str] = Field(default=None, max_length=10)
    birthday: Optional[date] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    permission_id: int = Field(gt=0)
    supervisor_id: Optional[int] = Field(default=None, gt=0)


class AccountUpdateRequest(CamelModel):
    sex: Optional[str] = Field(default=None, max_length=10)
    birthday: Optional[date] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    permission_id: Optional[int] = Field(default=None, gt=0)
    supervisor_id: Optional[int] = Field(default=None, gt=0)


class AccountApprovalRequest(CamelModel):
    approval_status: str = Field(pattern="^(已启用|已驳回|已停用)$")
    review_comment: Optional[str] = Field(default=None, max_length=255)
