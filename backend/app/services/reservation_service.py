from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def create_reservation(
        self,
        customer_id: int,
        room_type_id: int,
        operator_id: int,
        start_time: datetime,
        end_time: datetime,
        guest_count: int,
        prepay: Decimal,
    ) -> dict:
        now = datetime.now(start_time.tzinfo) if start_time.tzinfo else datetime.now()
        if start_time <= now:
            raise AppError(40002, "预定入住时间必须晚于当前时间")
        if start_time >= end_time:
            raise AppError(40002, "预定入住时间必须早于离店时间")
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)

        with transactional(self.db):
            reservation_id = self.repo.create_reservation_by_sp(
                customer_id,
                room_type_id,
                operator_id,
                start_time,
                end_time,
                guest_count,
                prepay,
            )
        return self.get_reservation(reservation_id)

    def list_reservations(
        self,
        page: int,
        page_size: int,
        customer_id: Optional[int] = None,
        card_id: Optional[str] = None,
        reservation_status: Optional[str] = None,
        room_type_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        return self.repo.list_reservations(
            page,
            page_size,
            customer_id,
            card_id,
            reservation_status,
            room_type_id,
            start_time,
            end_time,
        )

    def get_reservation(self, reservation_id: int) -> dict:
        reservation = self.repo.get_reservation(reservation_id)
        if reservation is None:
            raise not_found("预定订单")
        return reservation

    def cancel_reservation(self, reservation_id: int, operator_id: int) -> dict:
        reservation = self.get_reservation(reservation_id)
        if reservation["reservationStatus"] != "未入住":
            raise AppError(40901, "只有未入住预定可以取消")
        with transactional(self.db):
            self.repo.cancel_reservation(reservation_id)
            self.repo.try_add_operation_log(
                operator_id,
                "创建预定",
                "取消预定订单 %s" % reservation_id,
            )
        return self.get_reservation(reservation_id)
