import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_SERVER: str = os.getenv("DB_SERVER", r".\SQLEXPRESS")
    DB_NAME: str = os.getenv("DB_NAME", "dev_py")
    DB_USER: str | None = os.getenv("DB_USER")
    DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")
    DB_TRUSTED_CONNECTION: str = os.getenv("DB_TRUSTED_CONNECTION", "no")
    DB_ENCRYPT: str = os.getenv("DB_ENCRYPT", "no")
    DB_DRIVER: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

settings = Settings()
