from typing import Optional

from pydantic import Field

from app.schemas.common import CamelModel


class CustomerCreateRequest(CamelModel):
    customer_name: str = Field(min_length=1, max_length=50)
    card_id: str = Field(min_length=1, max_length=30)
    customer_phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=255)
    discount_id: int = Field(gt=0)


class CustomerUpdateRequest(CamelModel):
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    customer_phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=255)


class CustomerDiscountRequest(CamelModel):
    discount_id: int = Field(gt=0)
