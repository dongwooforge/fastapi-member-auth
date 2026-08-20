from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.model import RefreshToken


def revoke_all_refresh_tokens_by_user(
    db: Session,
    user_id: int
):
    now = datetime.now()

    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        )
        .all()
    )

    for token in tokens:
        token.revoked_at = now

    db.commit()
# Refresh Token 정보를 DB에 저장한다.
def create_refresh_token_record(
    db: Session,
    user_id: int,
    jti: str,
    expires_at: datetime
):
    refresh_token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return refresh_token


# jti로 Refresh Token 조회
def find_refresh_token_by_jti(
    db: Session,
    jti: str
):
    return (
        db.query(RefreshToken)
        .filter(RefreshToken.jti == jti)
        .first()
    )


# Refresh Token 폐기
def revoke_refresh_token(
    db: Session,
    refresh_token: RefreshToken
):
    # 폐기 시간을 기록한다.
    refresh_token.revoked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(refresh_token)

    return refresh_token