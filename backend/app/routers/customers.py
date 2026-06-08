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
from app.schemas.customers import (
    CustomerCreateRequest,
    CustomerDiscountRequest,
    CustomerUpdateRequest,
)
from app.services.customer_service import CustomerService


router = APIRouter(tags=["customers"])


@router.get("/discounts")
def list_discounts(
    request: Request,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    return success(request, CustomerService(db).list_discounts())


@router.post("/customers")
def create_customer(
    request: Request,
    payload: CustomerCreateRequest,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = CustomerService(db).create_customer(payload.model_dump(), current.account_id)
    return success(request, data, status_code=201)


@router.get("/customers")
def list_customers(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    cardId: Optional[str] = None,
    customerName: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    data = CustomerService(db).list_customers(page, pageSize, cardId, customerName, phone)
    return success(request, data)


@router.get("/customers/{customerId}")
def get_customer(
    request: Request,
    customerId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, CustomerService(db).get_customer(customerId))


@router.patch("/customers/{customerId}")
def update_customer(
    request: Request,
    payload: CustomerUpdateRequest,
    customerId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = CustomerService(db).update_customer(
        customerId,
        payload.model_dump(exclude_unset=True),
        current.account_id,
    )
    return success(request, data)


@router.patch("/customers/{customerId}/discount")
def update_customer_discount(
    request: Request,
    payload: CustomerDiscountRequest,
    customerId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = CustomerService(db).update_customer_discount(
        customerId,
        payload.discount_id,
        current.account_id,
    )
    return success(request, data)


@router.get("/customers/{customerId}/history")
def customer_history(
    request: Request,
    customerId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, CustomerService(db).customer_history(customerId))
