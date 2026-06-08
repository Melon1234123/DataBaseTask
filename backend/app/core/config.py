from dataclasses import dataclass
from functools import lru_cache
import os
from typing import List

from dotenv import load_dotenv


load_dotenv()


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "HotelSys Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = os.getenv(
        "HOTEL_DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/HotelSys?charset=utf8mb4",
    )
    jwt_secret_key: str = os.getenv(
        "HOTEL_JWT_SECRET_KEY",
        "dev-change-me-please-use-32-bytes-or-more",
    )
    jwt_algorithm: str = os.getenv("HOTEL_JWT_ALGORITHM", "HS256")
    access_token_expire_seconds: int = int(
        os.getenv("HOTEL_ACCESS_TOKEN_EXPIRE_SECONDS", "7200")
    )
    cors_origins: List[str] = None

    def __post_init__(self) -> None:
        origins = os.getenv(
            "HOTEL_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        )
        object.__setattr__(self, "cors_origins", _split_csv(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()
