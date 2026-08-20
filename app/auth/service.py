from datetime import datetime

from sqlalchemy.orm import Session

from app.auth import db


def save_refresh_token(
    session: Session,
    user_id: int,
    jti: str,
    expires_at: datetime
):
    return db.create_refresh_token_record(
        session,
        user_id,
        jti,
        expires_at
    )


def get_refresh_token_record(
    session: Session,
    jti: str
):
    return db.find_refresh_token_by_jti(
        session,
        jti
    )


# Refresh Token 폐기
def revoke_refresh_token(
    session: Session,
    jti: str
):
    token = db.find_refresh_token_by_jti(
        session,
        jti
    )

    # 존재하지 않는 토큰
    if token is None:
        return False

    # 이미 폐기된 토큰
    if token.revoked_at is not None:
        return False

    db.revoke_refresh_token(
        session,
        token
    )

    return True



def revoke_all_user_tokens(
    session: Session,
    user_id: int
):
    db.revoke_all_refresh_tokens_by_user(
        session,
        user_id
    )


