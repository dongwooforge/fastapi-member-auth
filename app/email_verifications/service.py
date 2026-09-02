from datetime import datetime, timedelta
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.email_verifications import db


# 인증번호 유효시간
VERIFICATION_EXPIRE_MINUTES = 5

# 최대 인증 시도 횟수
MAX_ATTEMPTS = 5


# 6자리 인증번호 생성
def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# 인증번호 Hash 생성
def hash_verification_code(code: str) -> str:
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


# 인증번호 발급
def create_email_verification(
    session: Session,
    email: str
):
    # 6자리 인증번호 생성
    code = generate_verification_code()

    # 원문 대신 Hash 저장
    code_hash = hash_verification_code(code)

    # 5분 후 만료
    expires_at = datetime.now() + timedelta(
        minutes=VERIFICATION_EXPIRE_MINUTES
    )

    db.create_verification(
        session,
        email,
        code_hash,
        expires_at
    )

    # 현재는 실제 이메일 발송 전 단계이므로
    # 테스트를 위해 인증번호를 반환한다.
    return code



def verify_email_code(
    session: Session,
    email: str,
    code: str
):
    # 가장 최근 인증 요청 조회
    verification = db.find_latest_verification(
        session,
        email
    )

    if verification is None:
        return "NOT_FOUND"

    # 이미 인증 완료
    if verification.verified_at is not None:
        return "ALREADY_VERIFIED"

    # 인증번호 만료
    if verification.expires_at < datetime.now():
        return "EXPIRED"

    # 최대 시도 횟수 초과
    if verification.attempt_count >= MAX_ATTEMPTS:
        return "TOO_MANY_ATTEMPTS"

    # 입력한 인증번호 Hash
    input_code_hash = hash_verification_code(
        code
    )

    # 인증번호 불일치
    if input_code_hash != verification.code_hash:
        verification.attempt_count += 1

        db.update_verification(
            session,
            verification
        )

        return "WRONG_CODE"

    # 인증 성공
    verification.verified_at = datetime.now()

    db.update_verification(
        session,
        verification
    )

    return "SUCCESS"

def is_email_verified(
    session: Session,
    email: str
) -> bool:
    verification = (
        db.find_valid_verified_verification(
            session,
            email
        )
    )

    return verification is not None