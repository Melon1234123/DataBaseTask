from pydantic import Field

from app.schemas.common import CamelModel


class LoginRequest(CamelModel):
    account_name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)
