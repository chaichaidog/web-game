import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

logger = logging.getLogger("nova.database")

_pg_server_instance = None

def resolve_database_url() -> str:
    global _pg_server_instance
    url = settings.RAW_DATABASE_URL.strip()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    if settings.USE_EMBEDDED_PG:
        try:
            import pgserver
            os.makedirs(settings.PG_DATA_DIR, exist_ok=True)
            _pg_server_instance = pgserver.get_server(settings.PG_DATA_DIR)
            uri = _pg_server_instance.get_uri()
            if uri.startswith("postgresql://"):
                uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
            logger.info(f"Connected to embedded PostgreSQL server at {settings.PG_DATA_DIR}")
            return uri
        except Exception as exc:
            logger.warning(f"Embedded PostgreSQL unavailable ({exc}); falling back to SQLite for local dev.")

    return "sqlite:///./nova_protocol_dev.db"

DATABASE_URL = resolve_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

