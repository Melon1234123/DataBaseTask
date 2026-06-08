from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.repositories.hotel_repository import HotelRepository
from app.services.helpers import transactional


class CleaningService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = HotelRepository(db)

    def list_tasks(
        self,
        page: int,
        page_size: int,
        clean_status=None,
        cleaner_id=None,
        include_unassigned=False,
    ) -> dict:
        return self.repo.list_cleaning_tasks(
            page,
            page_size,
            clean_status,
            cleaner_id,
            include_unassigned,
        )

    def start_task(self, task_id: int, cleaner_id: int) -> dict:
        with transactional(self.db):
            self.repo.start_cleaning_by_sp(task_id, cleaner_id)
        return self.get_task(task_id)

    def finish_task(self, task_id: int, cleaner_id: int) -> dict:
        with transactional(self.db):
            self.repo.finish_cleaning_by_sp(task_id, cleaner_id)
        return self.get_task(task_id)

    def assign_task(self, task_id: int, cleaner_id) -> dict:
        if self.repo.get_cleaning_task(task_id) is None:
            raise not_found("清扫任务")
        with transactional(self.db):
            self.repo.assign_cleaning_task(task_id, cleaner_id)
        return self.get_task(task_id)

    def get_task(self, task_id: int) -> dict:
        task = self.repo.get_cleaning_task(task_id)
        if task is None:
            raise not_found("清扫任务")
        return task

    @staticmethod
    def ensure_cleaner_self(cleaner_id: int, current_account_id: int) -> None:
        if cleaner_id != current_account_id:
            raise AppError(40301, "保洁员只能处理自己的清扫任务")
