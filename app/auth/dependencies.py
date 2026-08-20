from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)
from sqlalchemy.orm import Session

from app.auth.jwt import verify_access_token
from app.database.connection import get_db
from app.members import db as members_db


security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> int:
    # Authorization 헤더에서 JWT 추출
    token = credentials.credentials

    # JWT 자체 검증
    user_id, token_version = verify_access_token(
        token
    )

    # DB에서 현재 회원 조회
    user = members_db.find_member_by_id(
        db,
        user_id
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 사용자입니다."
        )

    # JWT 발급 당시 버전과 현재 DB 버전 비교
    if token_version != user.token_version:
        raise HTTPException(
            status_code=401,
            detail="만료된 로그인 정보입니다. 다시 로그인해주세요."
        )

    return user_id