import os
from collections.abc import Iterator

os.environ["JWT_SECRET"] = "test-only-secret-" + "x" * 32
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, configure_sqlite_engine, get_db
from app.main import app


@pytest.fixture
def db() -> Iterator[Session]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_engine(test_engine)
    Base.metadata.create_all(bind=test_engine)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        test_engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
