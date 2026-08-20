from fastapi import FastAPI

from app.database.connection import engine
from app.database.base import Base

from app.members.model import Member
from app.auth.model import RefreshToken

from app.members.router import router as members_router


# SQLAlchemy Model을 기반으로 테이블 생성
Base.metadata.create_all(bind=engine)


app = FastAPI()

app.include_router(members_router)