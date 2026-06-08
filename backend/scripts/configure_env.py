from getpass import getpass
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import quote


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"


def prompt(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def main() -> None:
    print("Create local backend/.env. This file is ignored by git.")
    host = prompt("MySQL host", "127.0.0.1")
    port = prompt("MySQL port", "3306")
    database = prompt("Database name", "HotelSys")
    user = prompt("MySQL user", "root")
    password = getpass("MySQL password: ")

    encoded_user = quote(user, safe="")
    encoded_password = quote(password, safe="")
    database_url = (
        f"mysql+pymysql://{encoded_user}:{encoded_password}"
        f"@{host}:{port}/{database}?charset=utf8mb4"
    )

    content = "\n".join(
        [
            f"HOTEL_DATABASE_URL={database_url}",
            f"HOTEL_JWT_SECRET_KEY={token_urlsafe(48)}",
            "HOTEL_ACCESS_TOKEN_EXPIRE_SECONDS=7200",
            "HOTEL_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000",
            "",
        ]
    )
    ENV_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {ENV_PATH}")
    print("Do not commit this file.")


if __name__ == "__main__":
    main()
