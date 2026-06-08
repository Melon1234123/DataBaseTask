from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.repositories.hotel_repository import HotelRepository
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(HotelRepository(db))
    return success(request, service.login(payload.account_name, payload.password))
