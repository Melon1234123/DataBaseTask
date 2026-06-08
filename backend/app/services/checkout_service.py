from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.repositories.hotel_repository import HotelRepository


class CheckoutService:
    def __init__(self, db: Session) -> None:
        self.repo = HotelRepository(db)

    def list_checkouts(
        self,
        page: int,
        page_size: int,
        customer_id=None,
        card_id=None,
        cashier_id=None,
        start_time=None,
        end_time=None,
    ) -> dict:
        return self.repo.list_checkouts(
            page,
            page_size,
            customer_id,
            card_id,
            cashier_id,
            start_time,
            end_time,
        )

    def get_checkout(self, checkout_id: int) -> dict:
        checkout = self.repo.get_checkout(checkout_id)
        if checkout is None:
            raise not_found("结账记录")
        return checkout
