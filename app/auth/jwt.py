from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from fastapi import HTTPException, status
from app.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
)


# Access Token 생성
def create_access_token(
    user_id: int,
    token_version: int
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "access",

        # Access Token 발급 당시 회원의 토큰 버전
        "token_version": token_version,

        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# Refresh Token 생성
def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)

    # 토큰마다 고유 ID 생성
    jti = str(uuid4())

    expires_at = now + timedelta(
        days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    # JWT뿐 아니라 DB 저장에 필요한 값도 함께 반환
    return token, jti, expires_at


# Access Token 검증
def verify_access_token(
    token: str
) -> tuple[int, int]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        token_type = payload.get("type")
        token_version = payload.get("token_version")

        if (
            user_id is None
            or token_type != "access"
            or token_version is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 Access Token입니다."
            )

        return int(user_id), int(token_version)

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Access Token입니다."
        )


# Refresh Token 검증
# user_id와 jti를 함께 반환한다.
def verify_refresh_token(token: str) -> tuple[int, str]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")

        if (
            user_id is None
            or token_type != "refresh"
            or jti is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 Refresh Token입니다."
            )

        return int(user_id), jti

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다."
        )