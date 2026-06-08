from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def db_key_to_camel(key: str) -> str:
    if not key:
        return key
    if "_" in key:
        parts = key.split("_")
        return parts[0].lower() + "".join(part.capitalize() for part in parts[1:])
    return key[0].lower() + key[1:]


def row_to_camel(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {db_key_to_camel(str(key)): value for key, value in dict(row).items()}


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def fetch_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[dict]:
        row = self.db.execute(text(sql), params or {}).mappings().first()
        return row_to_camel(row)

    def fetch_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[dict]:
        rows = self.db.execute(text(sql), params or {}).mappings().all()
        return [row_to_camel(row) for row in rows]

    def scalar(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.db.execute(text(sql), params or {}).scalar()

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        result = self.db.execute(text(sql), params or {})
        return int(result.rowcount or 0)

    def insert(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        result = self.db.execute(text(sql), params or {})
        return int(result.lastrowid)

    def page(
        self,
        select_sql: str,
        count_sql: str,
        params: Dict[str, Any],
        page: int,
        page_size: int,
        order_by: str,
        order: str = "desc",
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        safe_order = "asc" if order == "asc" else "desc"
        query_params = dict(params)
        query_params["limit"] = page_size
        query_params["offset"] = (page - 1) * page_size
        items = self.fetch_all(
            "%s ORDER BY %s %s LIMIT :limit OFFSET :offset"
            % (select_sql, order_by, safe_order),
            query_params,
        )
        total = int(self.scalar(count_sql, params) or 0)
        return {"items": items, "total": total, "page": page, "pageSize": page_size}
