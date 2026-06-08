from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, model_validator

from app.schemas.common import CamelModel


class CheckInCreateRequest(CamelModel):
    customer_id: int = Field(gt=0)
    room_id: int = Field(gt=0)
    reservation_id: Optional[int] = Field(default=None, gt=0)
    check_in_start_time: datetime
    check_in_end_time: Optional[datetime] = None
    guest_count: int = Field(gt=0)
    prepay_amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if (
            self.check_in_end_time is not None
            and self.check_in_start_time >= self.check_in_end_time
        ):
            raise ValueError("入住结束时间必须晚于开始时间")
        return self


class ChangeRoomRequest(CamelModel):
    new_room_id: int = Field(gt=0)
    old_room_clean_required: bool = True


class CheckoutCreateRequest(CamelModel):
    checkout_time: Optional[datetime] = None
