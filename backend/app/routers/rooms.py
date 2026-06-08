from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_AUDITOR,
    ROLE_CLEANER,
    ROLE_FRONT_DESK,
    AccountPrincipal,
    require_roles,
)
from app.core.responses import success
from app.schemas.rooms import (
    RoomCreateRequest,
    RoomTypeCreateRequest,
    RoomTypeUpdateRequest,
    RoomUpdateRequest,
)
from app.services.room_service import RoomService


router = APIRouter(tags=["rooms"])


@router.get("/room-types")
def list_room_types(
    request: Request,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, RoomService(db).list_room_types())


@router.post("/room-types")
def create_room_type(
    request: Request,
    payload: RoomTypeCreateRequest,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = RoomService(db).create_room_type(payload.model_dump(), current.account_id)
    return success(request, data, status_code=201)


@router.patch("/room-types/{roomTypeId}")
def update_room_type(
    request: Request,
    payload: RoomTypeUpdateRequest,
    roomTypeId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = RoomService(db).update_room_type(
        roomTypeId,
        payload.model_dump(exclude_unset=True),
        current.account_id,
    )
    return success(request, data)


@router.delete("/room-types/{roomTypeId}")
def delete_room_type(
    request: Request,
    roomTypeId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    RoomService(db).delete_room_type(roomTypeId, current.account_id)
    return success(request, None)


@router.get("/rooms")
def list_rooms(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    roomStatus: Optional[str] = None,
    roomTypeId: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(
        require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_CLEANER, ROLE_AUDITOR)
    ),
):
    data = RoomService(db).list_rooms(page, pageSize, roomStatus, roomTypeId)
    return success(request, data)


@router.post("/rooms")
def create_room(
    request: Request,
    payload: RoomCreateRequest,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = RoomService(db).create_room(payload.model_dump(), current.account_id)
    return success(request, data, status_code=201)


@router.get("/rooms/available")
def available_rooms(
    request: Request,
    roomTypeId: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK)),
):
    items = RoomService(db).available_rooms(roomTypeId)
    return success(
        request,
        {"items": items, "total": len(items), "page": 1, "pageSize": len(items)},
    )


@router.get("/rooms/status-overview")
def room_status_overview(
    request: Request,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_AUDITOR)),
):
    return success(request, RoomService(db).room_status_overview())


@router.patch("/rooms/{roomId}")
def update_room(
    request: Request,
    payload: RoomUpdateRequest,
    roomId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = RoomService(db).update_room(
        roomId,
        payload.model_dump(exclude_unset=True),
        current.account_id,
    )
    return success(request, data)


@router.delete("/rooms/{roomId}")
def delete_room(
    request: Request,
    roomId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    RoomService(db).delete_room(roomId, current.account_id)
    return success(request, None)
