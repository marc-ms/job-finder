from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

from src.config import settings


def _build_engine(database_url: str):
    url = make_url(database_url)
    is_sqlite = url.drivername.startswith("sqlite")

    if is_sqlite:
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    return create_engine(database_url, pool_pre_ping=True)


engine = _build_engine(settings.DATABASE_URL)


def init_db() -> None:
    from src.db import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
