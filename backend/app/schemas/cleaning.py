from typing import Optional

from pydantic import Field

from app.schemas.common import CamelModel


class CleaningAssignRequest(CamelModel):
    cleaner_id: Optional[int] = Field(default=None, gt=0)
