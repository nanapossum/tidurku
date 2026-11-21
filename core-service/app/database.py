
from sqlalchemy import create_engine, text

from .config import settings


# SQLite memerlukan konfigurasi khusus untuk koneksi
# yang digunakan oleh FastAPI.
connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)


def check_database_connection() -> bool:
    """Memastikan database dapat menerima query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
