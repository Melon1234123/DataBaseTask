from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_AUDITOR,
    ROLE_FRONT_DESK,
    AccountPrincipal,
    require_roles,
)
from app.core.responses import success
from app.services.checkout_service import CheckoutService


router = APIRouter(prefix="/checkouts", tags=["checkouts"])


@router.get("")
def list_checkouts(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    customerId: Optional[int] = Query(default=None, gt=0),
    cardId: Optional[str] = None,
    cashierId: Optional[int] = Query(default=None, gt=0),
    startTime: Optional[datetime] = None,
    endTime: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    data = CheckoutService(db).list_checkouts(
        page,
        pageSize,
        customerId,
        cardId,
        cashierId,
        startTime,
        endTime,
    )
    return success(request, data)


@router.get("/{checkoutId}")
def get_checkout(
    request: Request,
    checkoutId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, CheckoutService(db).get_checkout(checkoutId))
