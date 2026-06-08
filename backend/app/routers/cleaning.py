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
from app.schemas.cleaning import CleaningAssignRequest
from app.schemas.common import CleanerPayload
from app.services.cleaning_service import CleaningService


router = APIRouter(prefix="/cleaning-tasks", tags=["cleaning-tasks"])


@router.get("")
def list_cleaning_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    cleanStatus: Optional[str] = None,
    cleanerId: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(
        require_roles(ROLE_ADMIN, ROLE_FRONT_DESK, ROLE_CLEANER, ROLE_AUDITOR)
    ),
):
    include_unassigned = False
    if current.permission_name == ROLE_CLEANER:
        cleanerId = current.account_id
        include_unassigned = True
    data = CleaningService(db).list_tasks(
        page,
        pageSize,
        cleanStatus,
        cleanerId,
        include_unassigned,
    )
    return success(request, data)


@router.post("/{cleaningTaskId}/start")
def start_cleaning(
    request: Request,
    payload: CleanerPayload,
    cleaningTaskId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_CLEANER)),
):
    CleaningService.ensure_cleaner_self(payload.cleaner_id, current.account_id)
    data = CleaningService(db).start_task(cleaningTaskId, payload.cleaner_id)
    return success(request, data)


@router.post("/{cleaningTaskId}/finish")
def finish_cleaning(
    request: Request,
    payload: CleanerPayload,
    cleaningTaskId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_CLEANER)),
):
    CleaningService.ensure_cleaner_self(payload.cleaner_id, current.account_id)
    data = CleaningService(db).finish_task(cleaningTaskId, payload.cleaner_id)
    return success(request, data)


@router.patch("/{cleaningTaskId}/assign")
def assign_cleaning(
    request: Request,
    payload: CleaningAssignRequest,
    cleaningTaskId: int = Path(gt=0),
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN)),
):
    data = CleaningService(db).assign_task(cleaningTaskId, payload.cleaner_id)
    return success(request, data)
