from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class CheckInService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def check_in(
        self,
        customer_id: int,
        room_id: int,
        reservation_id: Optional[int],
        operator_id: int,
        start_time: datetime,
        end_time: Optional[datetime],
        guest_count: int,
        prepay: Decimal,
    ) -> dict:
        with transactional(self.db):
            checkin_id = self.repo.check_in_by_sp(
                customer_id,
                room_id,
                reservation_id,
                operator_id,
                start_time,
                end_time,
                guest_count,
                prepay,
            )
        return self.get_checkin(checkin_id)

    def list_checkins(
        self,
        page: int,
        page_size: int,
        customer_id=None,
        card_id=None,
        order_status=None,
        room_id=None,
        start_time=None,
        end_time=None,
    ) -> dict:
        return self.repo.list_checkins(
            page,
            page_size,
            customer_id,
            card_id,
            order_status,
            room_id,
            start_time,
            end_time,
        )

    def get_checkin(self, checkin_id: int) -> dict:
        checkin = self.repo.get_checkin(checkin_id)
        if checkin is None:
            raise not_found("入住订单")
        return checkin

    def change_room(
        self,
        checkin_id: int,
        new_room_id: int,
        old_room_clean_required: bool,
        operator_id: int,
    ) -> dict:
        with transactional(self.db):
            checkin = self.repo.lock_checkin(checkin_id)
            if checkin is None:
                raise not_found("入住订单")
            if checkin["orderStatus"] != "进行中":
                raise AppError(40901, "只有进行中的入住订单可以换房")

            old_room = self.repo.lock_room(checkin["roomId"])
            new_room = self.repo.lock_room(new_room_id)
            if old_room is None or new_room is None:
                raise not_found("客房")
            if new_room["roomStatus"] != "空闲":
                raise AppError(40901, "新客房当前不是空闲状态，不能换房")

            self.repo.change_checkin_room(checkin_id, new_room_id)
            self.repo.set_room_status(new_room_id, "已入住")
            if old_room_clean_required:
                self.repo.set_room_status(old_room["roomId"], "待清扫")
                self.repo.create_cleaning_task(old_room["roomId"], old_room["roomNo"])
            else:
                self.repo.set_room_status(old_room["roomId"], "空闲")
            self.repo.try_add_operation_log(
                operator_id,
                "换房",
                "入住订单 %s 从房间 %s 换至房间 %s"
                % (checkin_id, old_room["roomNo"], new_room["roomNo"]),
            )
        return self.get_checkin(checkin_id)

    def checkout(
        self, checkin_id: int, cashier_id: int, checkout_time: Optional[datetime]
    ) -> dict:
        checkout_time = checkout_time or datetime.now()
        if checkout_time.tzinfo is not None:
            checkout_time = checkout_time.replace(tzinfo=None)
        with transactional(self.db):
            checkout_id = self.repo.checkout_by_sp(checkin_id, cashier_id, checkout_time)
        checkout = self.repo.get_checkout(checkout_id)
        if checkout is None:
            raise not_found("结账记录")
        return checkout

    def delete_unchecked_in(self, checkin_id: int, operator_id: int) -> dict:
        with transactional(self.db):
            checkin = self.repo.lock_checkin(checkin_id)
            if checkin is None:
                raise not_found("入住订单")
            if checkin["orderStatus"] != "进行中":
                raise AppError(40901, "只能删除未结账的在住订单")
            if self.repo.checkout_exists(checkin_id):
                raise AppError(40901, "该入住订单已有结账记录，不能删除")

            room = self.repo.lock_room(checkin["roomId"])
            if room is None:
                raise not_found("客房")

            self.repo.delete_checkin(checkin_id)
            self.repo.set_room_status(room["roomId"], "空闲")
            if checkin.get("reservationId"):
                self.repo.set_reservation_status(checkin["reservationId"], "未入住")
            self.repo.try_add_operation_log(
                operator_id,
                "办理入住",
                "删除错误入住订单 %s，房间 %s 已恢复空闲"
                % (checkin_id, room["roomNo"]),
            )

        return {
            "checkInId": checkin_id,
            "deleted": True,
            "roomId": room["roomId"],
            "roomStatus": "空闲",
        }
