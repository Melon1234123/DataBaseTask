from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository


class HotelRepository(BaseRepository):
    ACCOUNT_SELECT = """
        SELECT
            ua.AccountId,
            ua.AccountName,
            ua.Sex,
            ua.Birthday,
            ua.Phone,
            ua.PermissionId,
            ap.PermissionName,
            ap.PermissionScope,
            ua.SupervisorId,
            ua.ApprovalStatus
        FROM UserAccount ua
        JOIN AccountPermission ap ON ua.PermissionId = ap.PermissionId
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_account_by_name(self, account_name: str) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT
                ua.AccountId,
                ua.AccountName,
                ua.PasswordHash,
                ua.PermissionId,
                ap.PermissionName,
                ua.ApprovalStatus
            FROM UserAccount ua
            JOIN AccountPermission ap ON ua.PermissionId = ap.PermissionId
            WHERE ua.AccountName = :account_name
            """,
            {"account_name": account_name},
        )

    def get_account(self, account_id: int) -> Optional[dict]:
        return self.fetch_one(
            self.ACCOUNT_SELECT + " WHERE ua.AccountId = :account_id",
            {"account_id": account_id},
        )

    def list_accounts(
        self,
        page: int,
        page_size: int,
        approval_status: Optional[str] = None,
        permission_id: Optional[int] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if approval_status:
            where.append("ua.ApprovalStatus = :approval_status")
            params["approval_status"] = approval_status
        if permission_id:
            where.append("ua.PermissionId = :permission_id")
            params["permission_id"] = permission_id
        where_sql = " WHERE " + " AND ".join(where)
        return self.page(
            self.ACCOUNT_SELECT + where_sql,
            "SELECT COUNT(*) FROM UserAccount ua" + where_sql,
            params,
            page,
            page_size,
            "ua.AccountId",
            "desc",
        )

    def create_account(self, payload: dict, password_hash: str) -> int:
        return self.insert(
            """
            INSERT INTO UserAccount(
                AccountName, PasswordHash, Sex, Birthday, Phone,
                PermissionId, SupervisorId, ApprovalStatus
            )
            VALUES (
                :account_name, :password_hash, :sex, :birthday, :phone,
                :permission_id, :supervisor_id, '待审核'
            )
            """,
            {**payload, "password_hash": password_hash},
        )

    def update_account(self, account_id: int, values: dict) -> int:
        columns = {
            "sex": "Sex",
            "birthday": "Birthday",
            "phone": "Phone",
            "permission_id": "PermissionId",
            "supervisor_id": "SupervisorId",
        }
        return self._update_by_map("UserAccount", "AccountId", account_id, values, columns)

    def approve_account(self, account_id: int, approval_status: str) -> int:
        return self.execute(
            """
            UPDATE UserAccount
            SET ApprovalStatus = :approval_status
            WHERE AccountId = :account_id
            """,
            {"account_id": account_id, "approval_status": approval_status},
        )

    def list_permissions(self) -> list:
        return self.fetch_all(
            """
            SELECT PermissionId, PermissionName, PermissionScope
            FROM AccountPermission
            ORDER BY PermissionId
            """
        )

    def list_discounts(self) -> list:
        return self.fetch_all(
            """
            SELECT DiscountId, DiscountGrade, DiscountRate
            FROM Discount
            ORDER BY DiscountGrade
            """
        )

    def get_discount(self, discount_id: int) -> Optional[dict]:
        return self.fetch_one(
            "SELECT DiscountId, DiscountGrade, DiscountRate FROM Discount WHERE DiscountId = :id",
            {"id": discount_id},
        )

    def create_customer(self, payload: dict) -> int:
        return self.insert(
            """
            INSERT INTO Customer(CustomerName, CardId, CustomerPhone, Address, DiscountId)
            VALUES(:customer_name, :card_id, :customer_phone, :address, :discount_id)
            """,
            payload,
        )

    def get_customer(self, customer_id: int) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT c.*, d.DiscountGrade, d.DiscountRate
            FROM Customer c
            JOIN Discount d ON c.DiscountId = d.DiscountId
            WHERE c.CustomerId = :customer_id
            """,
            {"customer_id": customer_id},
        )

    def list_customers(
        self,
        page: int,
        page_size: int,
        card_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if card_id:
            where.append("c.CardId = :card_id")
            params["card_id"] = card_id
        if customer_name:
            where.append("c.CustomerName LIKE :customer_name")
            params["customer_name"] = "%%%s%%" % customer_name
        if phone:
            where.append("c.CustomerPhone LIKE :phone")
            params["phone"] = "%%%s%%" % phone
        where_sql = " WHERE " + " AND ".join(where)
        select_sql = """
            SELECT c.*, d.DiscountGrade, d.DiscountRate
            FROM Customer c
            JOIN Discount d ON c.DiscountId = d.DiscountId
        """ + where_sql
        count_sql = "SELECT COUNT(*) FROM Customer c" + where_sql
        return self.page(select_sql, count_sql, params, page, page_size, "c.CustomerId", "desc")

    def update_customer(self, customer_id: int, values: dict) -> int:
        columns = {
            "customer_name": "CustomerName",
            "customer_phone": "CustomerPhone",
            "address": "Address",
        }
        return self._update_by_map("Customer", "CustomerId", customer_id, values, columns)

    def update_customer_discount(self, customer_id: int, discount_id: int) -> int:
        return self.execute(
            "UPDATE Customer SET DiscountId = :discount_id WHERE CustomerId = :customer_id",
            {"customer_id": customer_id, "discount_id": discount_id},
        )

    def customer_history(self, customer_id: int) -> dict:
        reservations = self.fetch_all(
            """
            SELECT *
            FROM v_reservation_detail
            WHERE CustomerId = :customer_id
            ORDER BY ReserveStartTime DESC
            """,
            {"customer_id": customer_id},
        )
        checkins = self.fetch_all(
            """
            SELECT ci.*, c.CustomerName, c.CardId, r.RoomNo, rt.RoomTypeName
            FROM CheckIn ci
            JOIN Customer c ON ci.CustomerId = c.CustomerId
            JOIN Room r ON ci.RoomId = r.RoomId
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            WHERE ci.CustomerId = :customer_id
            ORDER BY ci.CheckInStartTime DESC
            """,
            {"customer_id": customer_id},
        )
        checkouts = self.fetch_all(
            """
            SELECT co.*, c.CustomerName, c.CardId
            FROM Checkout co
            JOIN Customer c ON co.CustomerId = c.CustomerId
            WHERE co.CustomerId = :customer_id
            ORDER BY co.CheckoutTime DESC
            """,
            {"customer_id": customer_id},
        )
        return {"reservations": reservations, "checkIns": checkins, "checkouts": checkouts}

    def list_room_types(self) -> list:
        return self.fetch_all(
            """
            SELECT RoomTypeId, RoomTypeName, RoomPrice
            FROM RoomType
            ORDER BY RoomTypeId DESC
            """
        )

    def get_room_type(self, room_type_id: int) -> Optional[dict]:
        return self.fetch_one(
            "SELECT RoomTypeId, RoomTypeName, RoomPrice FROM RoomType WHERE RoomTypeId = :id",
            {"id": room_type_id},
        )

    def create_room_type(self, payload: dict) -> int:
        return self.insert(
            """
            INSERT INTO RoomType(RoomTypeName, RoomPrice)
            VALUES(:room_type_name, :room_price)
            """,
            payload,
        )

    def update_room_type(self, room_type_id: int, values: dict) -> int:
        return self._update_by_map(
            "RoomType",
            "RoomTypeId",
            room_type_id,
            values,
            {"room_type_name": "RoomTypeName", "room_price": "RoomPrice"},
        )

    def delete_room_type(self, room_type_id: int) -> int:
        return self.execute("DELETE FROM RoomType WHERE RoomTypeId = :id", {"id": room_type_id})

    def list_rooms(
        self,
        page: int,
        page_size: int,
        room_status: Optional[str] = None,
        room_type_id: Optional[int] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if room_status:
            where.append("r.RoomStatus = :room_status")
            params["room_status"] = room_status
        if room_type_id:
            where.append("r.RoomTypeId = :room_type_id")
            params["room_type_id"] = room_type_id
        where_sql = " WHERE " + " AND ".join(where)
        select_sql = """
            SELECT r.*, rt.RoomTypeName, rt.RoomPrice
            FROM Room r
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
        """ + where_sql
        count_sql = "SELECT COUNT(*) FROM Room r" + where_sql
        return self.page(select_sql, count_sql, params, page, page_size, "r.RoomId", "desc")

    def get_room(self, room_id: int) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT r.*, rt.RoomTypeName, rt.RoomPrice
            FROM Room r
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            WHERE r.RoomId = :room_id
            """,
            {"room_id": room_id},
        )

    def create_room(self, payload: dict) -> int:
        return self.insert(
            """
            INSERT INTO Room(RoomNo, FloorNo, RoomPhone, RoomTypeId, RoomStatus)
            VALUES(:room_no, :floor_no, :room_phone, :room_type_id, :room_status)
            """,
            payload,
        )

    def update_room(self, room_id: int, values: dict) -> int:
        return self._update_by_map(
            "Room",
            "RoomId",
            room_id,
            values,
            {
                "floor_no": "FloorNo",
                "room_phone": "RoomPhone",
                "room_type_id": "RoomTypeId",
                "room_status": "RoomStatus",
            },
        )

    def delete_room(self, room_id: int) -> int:
        return self.execute("DELETE FROM Room WHERE RoomId = :id", {"id": room_id})

    def available_rooms(self, room_type_id: Optional[int] = None) -> list:
        params: Dict[str, Any] = {}
        where = []
        if room_type_id:
            where.append("RoomTypeId = :room_type_id")
            params["room_type_id"] = room_type_id
        where_sql = " WHERE " + " AND ".join(where) if where else ""
        return self.fetch_all(
            "SELECT * FROM v_available_room%s ORDER BY RoomTypeName, RoomNo" % where_sql,
            params,
        )

    def room_status_overview(self) -> list:
        return self.fetch_all(
            "SELECT * FROM v_room_status_overview ORDER BY RoomTypeName, RoomStatus"
        )

    def create_reservation_by_sp(
        self,
        customer_id: int,
        room_type_id: int,
        operator_id: int,
        start_time: datetime,
        end_time: datetime,
        guest_count: int,
        prepay: Decimal,
    ) -> int:
        self.db.execute(
            text(
                """
                CALL sp_create_reservation(
                    :customer_id, :room_type_id, :operator_id,
                    :start_time, :end_time, :guest_count, :prepay,
                    @reservation_id
                )
                """
            ),
            {
                "customer_id": customer_id,
                "room_type_id": room_type_id,
                "operator_id": operator_id,
                "start_time": start_time,
                "end_time": end_time,
                "guest_count": guest_count,
                "prepay": prepay,
            },
        )
        return int(self.scalar("SELECT @reservation_id") or 0)

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
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if customer_id:
            where.append("rv.CustomerId = :customer_id")
            params["customer_id"] = customer_id
        if card_id:
            where.append("c.CardId = :card_id")
            params["card_id"] = card_id
        if reservation_status:
            where.append("rv.ReservationStatus = :reservation_status")
            params["reservation_status"] = reservation_status
        if room_type_id:
            where.append("rv.RoomTypeId = :room_type_id")
            params["room_type_id"] = room_type_id
        if start_time:
            where.append("rv.ReserveStartTime >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where.append("rv.ReserveStartTime <= :end_time")
            params["end_time"] = end_time
        where_sql = " WHERE " + " AND ".join(where)
        base_from = """
            FROM Reservation rv
            JOIN Customer c ON rv.CustomerId = c.CustomerId
            JOIN RoomType rt ON rv.RoomTypeId = rt.RoomTypeId
            JOIN UserAccount ua ON rv.OperatorId = ua.AccountId
        """
        select_sql = """
            SELECT
                rv.*, c.CustomerName, c.CardId, c.CustomerPhone,
                rt.RoomTypeName, ua.AccountName AS OperatorName
        """ + base_from + where_sql
        return self.page(
            select_sql,
            "SELECT COUNT(*) " + base_from + where_sql,
            params,
            page,
            page_size,
            "rv.ReserveStartTime",
            "desc",
        )

    def get_reservation(self, reservation_id: int) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT
                rv.*, c.CustomerName, c.CardId, c.CustomerPhone,
                rt.RoomTypeName, ua.AccountName AS OperatorName
            FROM Reservation rv
            JOIN Customer c ON rv.CustomerId = c.CustomerId
            JOIN RoomType rt ON rv.RoomTypeId = rt.RoomTypeId
            JOIN UserAccount ua ON rv.OperatorId = ua.AccountId
            WHERE rv.ReservationId = :reservation_id
            """,
            {"reservation_id": reservation_id},
        )

    def cancel_reservation(self, reservation_id: int) -> int:
        return self.execute(
            """
            UPDATE Reservation
            SET ReservationStatus = '已取消'
            WHERE ReservationId = :reservation_id AND ReservationStatus = '未入住'
            """,
            {"reservation_id": reservation_id},
        )

    def check_in_by_sp(
        self,
        customer_id: int,
        room_id: int,
        reservation_id: Optional[int],
        operator_id: int,
        start_time: datetime,
        end_time: Optional[datetime],
        guest_count: int,
        prepay: Decimal,
    ) -> int:
        self.db.execute(
            text(
                """
                CALL sp_check_in(
                    :customer_id, :room_id, :reservation_id, :operator_id,
                    :start_time, :end_time, :guest_count, :prepay,
                    @checkin_id
                )
                """
            ),
            {
                "customer_id": customer_id,
                "room_id": room_id,
                "reservation_id": reservation_id,
                "operator_id": operator_id,
                "start_time": start_time,
                "end_time": end_time,
                "guest_count": guest_count,
                "prepay": prepay,
            },
        )
        return int(self.scalar("SELECT @checkin_id") or 0)

    def list_checkins(
        self,
        page: int,
        page_size: int,
        customer_id: Optional[int] = None,
        card_id: Optional[str] = None,
        order_status: Optional[str] = None,
        room_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if customer_id:
            where.append("ci.CustomerId = :customer_id")
            params["customer_id"] = customer_id
        if card_id:
            where.append("c.CardId = :card_id")
            params["card_id"] = card_id
        if order_status:
            where.append("ci.OrderStatus = :order_status")
            params["order_status"] = order_status
        if room_id:
            where.append("ci.RoomId = :room_id")
            params["room_id"] = room_id
        if start_time:
            where.append("ci.CheckInStartTime >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where.append("ci.CheckInStartTime <= :end_time")
            params["end_time"] = end_time
        where_sql = " WHERE " + " AND ".join(where)
        base_from = """
            FROM CheckIn ci
            JOIN Customer c ON ci.CustomerId = c.CustomerId
            JOIN Room r ON ci.RoomId = r.RoomId
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            LEFT JOIN UserAccount ua ON ci.OperatorId = ua.AccountId
        """
        select_sql = """
            SELECT
                ci.*, c.CustomerName, c.CardId, r.RoomNo, rt.RoomTypeName,
                ua.AccountName AS OperatorName
        """ + base_from + where_sql
        return self.page(
            select_sql,
            "SELECT COUNT(*) " + base_from + where_sql,
            params,
            page,
            page_size,
            "ci.CheckInStartTime",
            "desc",
        )

    def get_checkin(self, checkin_id: int) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT
                ci.*, c.CustomerName, c.CardId, r.RoomNo, rt.RoomTypeName,
                ua.AccountName AS OperatorName
            FROM CheckIn ci
            JOIN Customer c ON ci.CustomerId = c.CustomerId
            JOIN Room r ON ci.RoomId = r.RoomId
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            LEFT JOIN UserAccount ua ON ci.OperatorId = ua.AccountId
            WHERE ci.CheckInId = :checkin_id
            """,
            {"checkin_id": checkin_id},
        )

    def lock_checkin(self, checkin_id: int) -> Optional[dict]:
        return self.fetch_one(
            "SELECT * FROM CheckIn WHERE CheckInId = :checkin_id FOR UPDATE",
            {"checkin_id": checkin_id},
        )

    def lock_room(self, room_id: int) -> Optional[dict]:
        return self.fetch_one(
            "SELECT * FROM Room WHERE RoomId = :room_id FOR UPDATE",
            {"room_id": room_id},
        )

    def change_checkin_room(self, checkin_id: int, new_room_id: int) -> int:
        return self.execute(
            "UPDATE CheckIn SET RoomId = :new_room_id WHERE CheckInId = :checkin_id",
            {"checkin_id": checkin_id, "new_room_id": new_room_id},
        )

    def checkout_exists(self, checkin_id: int) -> bool:
        return bool(
            self.scalar(
                "SELECT COUNT(*) FROM Checkout WHERE CheckInId = :checkin_id",
                {"checkin_id": checkin_id},
            )
        )

    def delete_checkin(self, checkin_id: int) -> int:
        return self.execute(
            "DELETE FROM CheckIn WHERE CheckInId = :checkin_id",
            {"checkin_id": checkin_id},
        )

    def set_reservation_status(self, reservation_id: int, reservation_status: str) -> int:
        return self.execute(
            """
            UPDATE Reservation
            SET ReservationStatus = :reservation_status
            WHERE ReservationId = :reservation_id
            """,
            {"reservation_id": reservation_id, "reservation_status": reservation_status},
        )

    def set_room_status(self, room_id: int, room_status: str) -> int:
        return self.execute(
            "UPDATE Room SET RoomStatus = :room_status WHERE RoomId = :room_id",
            {"room_id": room_id, "room_status": room_status},
        )

    def create_cleaning_task(self, room_id: int, room_no: str) -> int:
        return self.insert(
            """
            INSERT INTO CleaningTask(RoomId, RoomNo, CleanStatus)
            VALUES(:room_id, :room_no, '待清扫')
            ON DUPLICATE KEY UPDATE
                RoomNo = VALUES(RoomNo),
                CleanStatus = '待清扫'
            """,
            {"room_id": room_id, "room_no": room_no},
        )

    def delete_unfinished_cleaning_tasks_for_room(self, room_id: int) -> int:
        return self.execute(
            """
            DELETE FROM CleaningTask
            WHERE RoomId = :room_id
              AND CleanStatus <> '已完成'
            """,
            {"room_id": room_id},
        )

    def checkout_by_sp(
        self, checkin_id: int, cashier_id: int, checkout_time: datetime
    ) -> int:
        self.db.execute(
            text(
                """
                CALL sp_checkout(
                    :checkin_id, :cashier_id, :checkout_time, @checkout_id
                )
                """
            ),
            {
                "checkin_id": checkin_id,
                "cashier_id": cashier_id,
                "checkout_time": checkout_time,
            },
        )
        return int(self.scalar("SELECT @checkout_id") or 0)

    def list_checkouts(
        self,
        page: int,
        page_size: int,
        customer_id: Optional[int] = None,
        card_id: Optional[str] = None,
        cashier_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if customer_id:
            where.append("co.CustomerId = :customer_id")
            params["customer_id"] = customer_id
        if card_id:
            where.append("c.CardId = :card_id")
            params["card_id"] = card_id
        if cashier_id:
            where.append("co.CashierId = :cashier_id")
            params["cashier_id"] = cashier_id
        if start_time:
            where.append("co.CheckoutTime >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where.append("co.CheckoutTime <= :end_time")
            params["end_time"] = end_time
        where_sql = " WHERE " + " AND ".join(where)
        base_from = """
            FROM Checkout co
            JOIN Customer c ON co.CustomerId = c.CustomerId
            JOIN UserAccount ua ON co.CashierId = ua.AccountId
        """
        select_sql = """
            SELECT
                co.*, c.CustomerName, c.CardId, ua.AccountName AS CashierName
        """ + base_from + where_sql
        return self.page(
            select_sql,
            "SELECT COUNT(*) " + base_from + where_sql,
            params,
            page,
            page_size,
            "co.CheckoutTime",
            "desc",
        )

    def get_checkout(self, checkout_id: int) -> Optional[dict]:
        return self.fetch_one(
            """
            SELECT
                co.*, c.CustomerName, c.CardId, ua.AccountName AS CashierName
            FROM Checkout co
            JOIN Customer c ON co.CustomerId = c.CustomerId
            JOIN UserAccount ua ON co.CashierId = ua.AccountId
            WHERE co.CheckoutId = :checkout_id
            """,
            {"checkout_id": checkout_id},
        )

    def list_cleaning_tasks(
        self,
        page: int,
        page_size: int,
        clean_status: Optional[str] = None,
        cleaner_id: Optional[int] = None,
        include_unassigned: bool = False,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if clean_status:
            where.append("CleanStatus = :clean_status")
            params["clean_status"] = clean_status
        if cleaner_id and include_unassigned:
            where.append("(CleanerId = :cleaner_id OR CleanerId IS NULL)")
            params["cleaner_id"] = cleaner_id
        elif cleaner_id:
            where.append("CleanerId = :cleaner_id")
            params["cleaner_id"] = cleaner_id
        where_sql = " WHERE " + " AND ".join(where)
        return self.page(
            "SELECT * FROM v_cleaning_task_queue" + where_sql,
            "SELECT COUNT(*) FROM v_cleaning_task_queue" + where_sql,
            params,
            page,
            page_size,
            "TaskCreateTime",
            "desc",
        )

    def get_cleaning_task(self, task_id: int) -> Optional[dict]:
        return self.fetch_one(
            "SELECT * FROM CleaningTask WHERE CleaningTaskId = :task_id",
            {"task_id": task_id},
        )

    def start_cleaning_by_sp(self, task_id: int, cleaner_id: int) -> None:
        self.db.execute(
            text("CALL sp_start_cleaning(:task_id, :cleaner_id)"),
            {"task_id": task_id, "cleaner_id": cleaner_id},
        )

    def finish_cleaning_by_sp(self, task_id: int, cleaner_id: int) -> None:
        self.db.execute(
            text("CALL sp_finish_cleaning(:task_id, :cleaner_id)"),
            {"task_id": task_id, "cleaner_id": cleaner_id},
        )

    def assign_cleaning_task(self, task_id: int, cleaner_id: Optional[int]) -> int:
        return self.execute(
            "UPDATE CleaningTask SET CleanerId = :cleaner_id WHERE CleaningTaskId = :task_id",
            {"task_id": task_id, "cleaner_id": cleaner_id},
        )

    def list_operation_types(self) -> list:
        return self.fetch_all(
            """
            SELECT OperationTypeId, OperationTypeName
            FROM OperationType
            ORDER BY OperationTypeId
            """
        )

    def list_operation_logs(
        self,
        page: int,
        page_size: int,
        operator_id: Optional[int] = None,
        operation_type_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        where = ["1=1"]
        params: Dict[str, Any] = {}
        if operator_id:
            where.append("AccountId = :operator_id")
            params["operator_id"] = operator_id
        if operation_type_name:
            where.append("OperationTypeName = :operation_type_name")
            params["operation_type_name"] = operation_type_name
        if start_time:
            where.append("OperationTime >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where.append("OperationTime <= :end_time")
            params["end_time"] = end_time
        where_sql = " WHERE " + " AND ".join(where)
        return self.page(
            "SELECT * FROM v_operation_audit" + where_sql,
            "SELECT COUNT(*) FROM v_operation_audit" + where_sql,
            params,
            page,
            page_size,
            "OperationTime",
            "desc",
        )

    def add_operation_log(
        self, operator_id: int, operation_type_name: str, operation_info: str
    ) -> None:
        self.db.execute(
            text(
                """
                CALL sp_add_operation_log(
                    :operator_id, :operation_type_name, :operation_info
                )
                """
            ),
            {
                "operator_id": operator_id,
                "operation_type_name": operation_type_name,
                "operation_info": operation_info,
            },
        )

    def try_add_operation_log(
        self, operator_id: int, operation_type_name: str, operation_info: str
    ) -> None:
        try:
            self.add_operation_log(operator_id, operation_type_name, operation_info)
        except SQLAlchemyError as exc:
            if operation_type_name == "换房" and "操作类型不存在" in str(exc):
                self.add_operation_log(operator_id, "办理入住", operation_info)
                return
            raise

    def _update_by_map(
        self,
        table_name: str,
        pk_name: str,
        pk_value: int,
        values: dict,
        columns: Dict[str, str],
    ) -> int:
        selected = {
            key: value for key, value in values.items() if key in columns and value is not None
        }
        if not selected:
            return 0
        assignments = ", ".join("%s = :%s" % (columns[key], key) for key in selected)
        params = dict(selected)
        params["pk_value"] = pk_value
        sql = "UPDATE %s SET %s WHERE %s = :pk_value" % (table_name, assignments, pk_name)
        return self.execute(sql, params)
