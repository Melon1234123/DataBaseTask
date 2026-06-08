from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, model_validator

from app.schemas.common import CamelModel


class ReservationCreateRequest(CamelModel):
    customer_id: int = Field(gt=0)
    room_type_id: int = Field(gt=0)
    reserve_start_time: datetime
    reserve_end_time: datetime
    guest_count: int = Field(gt=0)
    prepay_amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.reserve_start_time >= self.reserve_end_time:
            raise ValueError("预定开始时间必须早于结束时间")
        return self


class ReservationCancelRequest(CamelModel):
    cancel_reason: Optional[str] = Field(default=None, max_length=255)
