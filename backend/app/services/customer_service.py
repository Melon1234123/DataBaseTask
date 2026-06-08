from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def list_discounts(self) -> list:
        return self.repo.list_discounts()

    def create_customer(self, payload: dict, operator_id: int) -> dict:
        if self.repo.get_discount(payload["discount_id"]) is None:
            raise AppError(40002, "折扣等级不存在")
        with transactional(self.db):
            customer_id = self.repo.create_customer(payload)
            self.repo.try_add_operation_log(
                operator_id,
                "客户维护",
                "新增客户 %s" % payload["customer_name"],
            )
        return self.get_customer(customer_id)

    def list_customers(self, page: int, page_size: int, card_id=None, customer_name=None, phone=None):
        return self.repo.list_customers(page, page_size, card_id, customer_name, phone)

    def get_customer(self, customer_id: int) -> dict:
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise not_found("客户")
        return customer

    def update_customer(self, customer_id: int, values: dict, operator_id: int) -> dict:
        self.get_customer(customer_id)
        with transactional(self.db):
            self.repo.update_customer(customer_id, values)
            self.repo.try_add_operation_log(operator_id, "客户维护", "修改客户 %s" % customer_id)
        return self.get_customer(customer_id)

    def update_customer_discount(self, customer_id: int, discount_id: int, operator_id: int) -> dict:
        self.get_customer(customer_id)
        if self.repo.get_discount(discount_id) is None:
            raise AppError(40002, "折扣等级不存在")
        with transactional(self.db):
            self.repo.update_customer_discount(customer_id, discount_id)
            self.repo.try_add_operation_log(
                operator_id,
                "客户维护",
                "修改客户 %s 折扣等级为 %s" % (customer_id, discount_id),
            )
        return self.get_customer(customer_id)

    def customer_history(self, customer_id: int) -> dict:
        self.get_customer(customer_id)
        return self.repo.customer_history(customer_id)
