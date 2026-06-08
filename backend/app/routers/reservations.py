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
from app.schemas.reservations import ReservationCancelRequest, ReservationCreateRequest
from app.services.reservation_service import ReservationService


router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("")
def create_reservation(
    request: Request,
    payload: ReservationCreateRequest,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = ReservationService(db).create_reservation(
        payload.customer_id,
        payload.room_type_id,
        current.account_id,
        payload.reserve_start_time,
        payload.reserve_end_time,
        payload.guest_count,
        payload.prepay_amount,
    )
    return success(request, data, status_code=201)


@router.get("")
def list_reservations(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    customerId: Optional[int] = Query(default=None, gt=0),
    cardId: Optional[str] = None,
    reservationStatus: Optional[str] = None,
    roomTypeId: Optional[int] = Query(default=None, gt=0),
    startTime: Optional[datetime] = None,
    endTime: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    data = ReservationService(db).list_reservations(
        page,
        pageSize,
        customerId,
        cardId,
        reservationStatus,
        roomTypeId,
        startTime,
        endTime,
    )
    return success(request, data)


@router.get("/{reservationId}")
def get_reservation(
    request: Request,
    reservationId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, ReservationService(db).get_reservation(reservationId))


@router.patch("/{reservationId}/cancel")
def cancel_reservation(
    request: Request,
    payload: ReservationCancelRequest,
    reservationId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = ReservationService(db).cancel_reservation(reservationId, current.account_id)
    return success(request, data)
