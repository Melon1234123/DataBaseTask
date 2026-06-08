from sqlalchemy.orm import Session

from app.repositories.hotel_repository import HotelRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.repo = HotelRepository(db)

    def list_operation_types(self) -> list:
        return self.repo.list_operation_types()

    def list_operation_logs(
        self,
        page: int,
        page_size: int,
        operator_id=None,
        operation_type_name=None,
        start_time=None,
        end_time=None,
    ) -> dict:
        return self.repo.list_operation_logs(
            page,
            page_size,
            operator_id,
            operation_type_name,
            start_time,
            end_time,
        )
