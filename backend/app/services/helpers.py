from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError, translate_db_error


@contextmanager
def transactional(db: Session):
    try:
        yield
        db.commit()
    except AppError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise translate_db_error(exc)
