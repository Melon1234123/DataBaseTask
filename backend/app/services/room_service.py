from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def list_room_types(self) -> list:
        return self.repo.list_room_types()

    def create_room_type(self, payload: dict, operator_id: int) -> dict:
        with transactional(self.db):
            room_type_id = self.repo.create_room_type(payload)
            self.repo.try_add_operation_log(
                operator_id,
                "客房维护",
                "新增房型 %s" % payload["room_type_name"],
            )
        return self.get_room_type(room_type_id)

    def get_room_type(self, room_type_id: int) -> dict:
        room_type = self.repo.get_room_type(room_type_id)
        if room_type is None:
            raise not_found("房型")
        return room_type

    def update_room_type(self, room_type_id: int, values: dict, operator_id: int) -> dict:
        self.get_room_type(room_type_id)
        with transactional(self.db):
            self.repo.update_room_type(room_type_id, values)
            self.repo.try_add_operation_log(operator_id, "客房维护", "修改房型 %s" % room_type_id)
        return self.get_room_type(room_type_id)

    def delete_room_type(self, room_type_id: int, operator_id: int) -> None:
        self.get_room_type(room_type_id)
        with transactional(self.db):
            self.repo.delete_room_type(room_type_id)
            self.repo.try_add_operation_log(operator_id, "客房维护", "删除房型 %s" % room_type_id)

    def list_rooms(self, page: int, page_size: int, room_status=None, room_type_id=None):
        return self.repo.list_rooms(page, page_size, room_status, room_type_id)

    def get_room(self, room_id: int) -> dict:
        room = self.repo.get_room(room_id)
        if room is None:
            raise not_found("客房")
        return room

    def create_room(self, payload: dict, operator_id: int) -> dict:
        with transactional(self.db):
            room_id = self.repo.create_room(payload)
            self.repo.try_add_operation_log(operator_id, "客房维护", "新增客房 %s" % payload["room_no"])
        return self.get_room(room_id)

    def update_room(self, room_id: int, values: dict, operator_id: int) -> dict:
        room = self.get_room(room_id)
        next_status = values.get("room_status")
        if next_status and room["roomStatus"] == "已入住" and next_status != "已入住":
            raise AppError(40901, "该房间存在未结账入住订单，请先到入住结账页面完成结账")
        with transactional(self.db):
            deleted_cleaning_count = 0
            if room["roomStatus"] == "待清扫" and next_status in ("空闲", "停用"):
                deleted_cleaning_count = self.repo.delete_unfinished_cleaning_tasks_for_room(
                    room_id
                )
            self.repo.update_room(room_id, values)
            log_detail = "修改客房 %s" % room_id
            if deleted_cleaning_count:
                log_detail += "，同步删除未完成清扫任务 %s 个" % deleted_cleaning_count
            self.repo.try_add_operation_log(operator_id, "客房维护", log_detail)
        return self.get_room(room_id)

    def delete_room(self, room_id: int, operator_id: int) -> None:
        self.get_room(room_id)
        with transactional(self.db):
            self.repo.delete_room(room_id)
            self.repo.try_add_operation_log(operator_id, "客房维护", "删除客房 %s" % room_id)

    def available_rooms(self, room_type_id=None) -> list:
        return self.repo.available_rooms(room_type_id)

    def room_status_overview(self) -> list:
        return self.repo.room_status_overview()
