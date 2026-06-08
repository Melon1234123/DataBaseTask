from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.schemas.common import CamelModel


class RoomTypeCreateRequest(CamelModel):
    room_type_name: str = Field(min_length=1, max_length=50)
    room_price: Decimal = Field(ge=0)


class RoomTypeUpdateRequest(CamelModel):
    room_type_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    room_price: Optional[Decimal] = Field(default=None, ge=0)


class RoomCreateRequest(CamelModel):
    room_no: str = Field(min_length=1, max_length=30)
    floor_no: Optional[int] = None
    room_phone: Optional[str] = Field(default=None, max_length=30)
    room_type_id: int = Field(gt=0)
    room_status: str = Field(default="空闲", pattern="^(空闲|已预定|已入住|待清扫|停用)$")


class RoomUpdateRequest(CamelModel):
    floor_no: Optional[int] = None
    room_phone: Optional[str] = Field(default=None, max_length=30)
    room_type_id: Optional[int] = Field(default=None, gt=0)
    room_status: Optional[str] = Field(
        default=None, pattern="^(空闲|已预定|已入住|待清扫|停用)$"
    )
