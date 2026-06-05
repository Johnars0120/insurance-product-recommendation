from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "insurance_recommendation.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE.as_posix()}"

_engine = None
SessionLocal = None


def configure_database(database_url=DATABASE_URL):
    global _engine, SessionLocal

    connect_args = {}
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        connect_args = {"check_same_thread": False}

    if _engine is not None:
        _engine.dispose()

    _engine = create_engine(database_url, connect_args=connect_args)
    if is_sqlite:
        event.listen(_engine, "connect", _enable_sqlite_foreign_keys)

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        expire_on_commit=False,
    )
    return _engine


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def get_engine():
    if _engine is None:
        configure_database()
    return _engine


def create_tables():
    from app.models.database_models import Base

    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_session():
    if SessionLocal is None:
        configure_database()

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
