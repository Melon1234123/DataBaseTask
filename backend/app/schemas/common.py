from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PaginationParams(CamelModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: Optional[str] = None
    order: str = Field(default="desc", pattern="^(asc|desc)$")


class TimeRangeParams(CamelModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class CleanerPayload(CamelModel):
    cleaner_id: int = Field(gt=0)


class DecimalMoneyModel(CamelModel):
    @field_validator("*", mode="before")
    @classmethod
    def parse_decimal(cls, value):
        if isinstance(value, str):
            return Decimal(value)
        return value
