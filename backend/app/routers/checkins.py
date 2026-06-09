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
from app.schemas.checkins import ChangeRoomRequest, CheckInCreateRequest, CheckoutCreateRequest
from app.services.checkin_service import CheckInService


router = APIRouter(prefix="/check-ins", tags=["check-ins"])


@router.post("")
def check_in(
    request: Request,
    payload: CheckInCreateRequest,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = CheckInService(db).check_in(
        payload.customer_id,
        payload.room_id,
        payload.reservation_id,
        current.account_id,
        payload.check_in_start_time,
        payload.check_in_end_time,
        payload.guest_count,
        payload.prepay_amount,
    )
    return success(request, data, status_code=201)


@router.get("")
def list_checkins(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    customerId: Optional[int] = Query(default=None, gt=0),
    cardId: Optional[str] = None,
    orderStatus: Optional[str] = None,
    roomId: Optional[int] = Query(default=None, gt=0),
    startTime: Optional[datetime] = None,
    endTime: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    data = CheckInService(db).list_checkins(
        page,
        pageSize,
        customerId,
        cardId,
        orderStatus,
        roomId,
        startTime,
        endTime,
    )
    return success(request, data)


@router.get("/{checkInId}")
def get_checkin(
    request: Request,
    checkInId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, CheckInService(db).get_checkin(checkInId))


@router.post("/{checkInId}/change-room")
def change_room(
    request: Request,
    payload: ChangeRoomRequest,
    checkInId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = CheckInService(db).change_room(
        checkInId,
        payload.new_room_id,
        payload.old_room_clean_required,
        current.account_id,
    )
    return success(request, data)


@router.post("/{checkInId}/checkout")
def checkout(
    request: Request,
    payload: CheckoutCreateRequest,
    checkInId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    data = CheckInService(db).checkout(checkInId, current.account_id, payload.checkout_time)
    return success(request, data, status_code=201)
