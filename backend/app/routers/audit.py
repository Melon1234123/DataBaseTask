from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_AUDITOR, AccountPrincipal, require_roles
from app.core.responses import success
from app.services.audit_service import AuditService


router = APIRouter(tags=["audit"])


@router.get("/operation-types")
def list_operation_types(
    request: Request,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_AUDITOR)),
):
    return success(request, AuditService(db).list_operation_types())


@router.get("/operation-logs")
def list_operation_logs(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    operatorId: Optional[int] = Query(default=None, gt=0),
    operationTypeName: Optional[str] = None,
    startTime: Optional[datetime] = None,
    endTime: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current: AccountPrincipal = Depends(require_roles(ROLE_ADMIN, ROLE_AUDITOR)),
):
    data = AuditService(db).list_operation_logs(
        page,
        pageSize,
        operatorId,
        operationTypeName,
        startTime,
        endTime,
    )
    return success(request, data)
