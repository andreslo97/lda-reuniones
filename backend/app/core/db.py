from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from .config import settings

def build_connection_url() -> URL:
    driver = settings.DB_DRIVER

    if settings.DB_TRUSTED_CONNECTION.lower() == "yes":
        return URL.create(
            "mssql+pyodbc",
            host=settings.DB_SERVER,
            database=settings.DB_NAME,
            query={
                "driver": driver,
                "Trusted_Connection": "Yes",
                "Encrypt": "Yes" if settings.DB_ENCRYPT.lower() == "yes" else "No",
                "TrustServerCertificate": "Yes",
            },
        )

    return URL.create(
        "mssql+pyodbc",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_SERVER,
        database=settings.DB_NAME,
        query={
            "driver": driver,
            "Encrypt": "Yes" if settings.DB_ENCRYPT.lower() == "yes" else "No",
            "TrustServerCertificate": "Yes",
        },
    )

engine = create_engine(build_connection_url(), pool_pre_ping=True, future=True)
