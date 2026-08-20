from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL


# MySQL 연결 객체
engine = create_engine(DATABASE_URL)


# DB Session 생성기
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# API 요청마다 DB Session을 생성한다.
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()




# 환경변수 설정 변경 필요
"""
mysql+pymysql → MySQL + PyMySQL 사용
fastapi       → DB 사용자
fastapi       → DB 비밀번호
127.0.0.1     → 내 컴퓨터
3306          → MySQL 포트
fastapi_db    → 사용할 데이터베이스
"""