import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.connection import get_db
from app.config import TEST_DATABASE_URL



# 테스트 DB 전용 Engine
test_engine = create_engine(
    TEST_DATABASE_URL
)


# 테스트 DB 전용 Session 생성기
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


@pytest.fixture()
def db():
    """
    각 테스트마다 깨끗한 DB를 준비한다.
    """

    # 테스트 시작 전 테이블 생성
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        # 테스트가 끝나면 모든 테이블 삭제
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db):
    """
    FastAPI의 실제 get_db를
    테스트 DB용 Session으로 교체한다.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Dependency Override
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 테스트 종료 후 원래 Dependency 상태로 복구
    app.dependency_overrides.clear()