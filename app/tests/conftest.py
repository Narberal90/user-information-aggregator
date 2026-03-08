import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Встановлюємо SQLite ДО імпорту app — щоб database.py не намагався підключитись до PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["API_BASE_URL"] = "https://dummyjson.com"
os.environ["FETCH_CHUNK_SIZE"] = "10"
os.environ["API_KEY"] = "test-api-key"
os.environ["FETCH_USERS_INTERVAL"] = "10"
os.environ["FETCH_POSTS_INTERVAL"] = "15"
os.environ["FETCH_COMMENTS_INTERVAL"] = "20"

from app.db.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = "sqlite:///./test.db"

engine_test = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as c:
        yield c
    app.dependency_overrides.clear()
