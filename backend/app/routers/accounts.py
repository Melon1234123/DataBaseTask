from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import ROLE_ADMIN, AccountPrincipal, require_roles
from app.core.responses import success
from app.schemas.accounts import (
    AccountApprovalRequest,
    AccountRegisterRequest,
    AccountUpdateRequest,
)
from app.services.account_service import AccountService


router = APIRouter(tags=["accounts"])


@router.post("/accounts/register")
def register(request: Request, payload: AccountRegisterRequest, db: Session = Depends(get_db)):
    account = AccountService(db).register(payload.model_dump())
    return success(request, account, status_code=201)


@router.get("/accounts")
def list_accounts(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    approvalStatus: Optional[str] = None,
    permissionId: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = AccountService(db).list_accounts(page, pageSize, approvalStatus, permissionId)
    return success(request, data)


@router.get("/accounts/{accountId}")
def get_account(
    request: Request,
    accountId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    return success(request, AccountService(db).get_account(accountId))


@router.patch("/accounts/{accountId}")
def update_account(
    request: Request,
    payload: AccountUpdateRequest,
    accountId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = AccountService(db).update_account(accountId, payload.model_dump(exclude_unset=True))
    return success(request, data)


@router.patch("/accounts/{accountId}/approval")
def approve_account(
    request: Request,
    payload: AccountApprovalRequest,
    accountId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = AccountService(db).approve_account(accountId, payload.approval_status)
    return success(request, data)


@router.get("/permissions")
def list_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    return success(request, AccountService(db).list_permissions())
