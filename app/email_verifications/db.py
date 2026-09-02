from sqlalchemy.orm import Session

from app.email_verifications.model import EmailVerification


# 가장 최근 이메일 인증 요청 조회
def find_latest_verification(
    db: Session,
    email: str
):
    return (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email
        )
        .order_by(
            EmailVerification.created_at.desc()
        )
        .first()
    )


# 인증 요청 저장
def create_verification(
    db: Session,
    email: str,
    code_hash: str,
    expires_at
):
    verification = EmailVerification(
        email=email,
        code_hash=code_hash,
        expires_at=expires_at
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    return verification


# 인증 요청 상태 저장
def update_verification(
    db: Session,
    verification: EmailVerification
):
    db.commit()
    db.refresh(verification)

    return verification


from datetime import datetime


def find_valid_verified_verification(
    db: Session,
    email: str
):
    return (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email,
            EmailVerification.verified_at.is_not(None),
            EmailVerification.expires_at > datetime.now()
        )
        .order_by(
            EmailVerification.created_at.desc()
        )
        .first()
    )