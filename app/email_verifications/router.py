from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.email_verifications.schema import (
    EmailVerificationRequest,
    EmailVerificationConfirm
)
from app.email_verifications.service import (
    create_email_verification,
    verify_email_code
)


router = APIRouter()


# 이메일 인증번호 발급
@router.post("/email-verifications")
def request_email_verification(
    data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    code = create_email_verification(
        db,
        data.email
    )

    # 실제 메일 발송을 붙이면 code는 응답에서 제거해야 한다.
    return {
        "message": "인증번호가 생성되었습니다.",
        "verification_code": code
    }


# 이메일 인증번호 확인
@router.post("/email-verifications/verify")
def confirm_email_verification(
    data: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    result = verify_email_code(
        db,
        data.email,
        data.code
    )

    if result == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="이메일 인증 요청을 찾을 수 없습니다."
        )

    if result == "ALREADY_VERIFIED":
        raise HTTPException(
            status_code=409,
            detail="이미 인증된 이메일입니다."
        )

    if result == "EXPIRED":
        raise HTTPException(
            status_code=400,
            detail="인증번호가 만료되었습니다."
        )

    if result == "TOO_MANY_ATTEMPTS":
        raise HTTPException(
            status_code=429,
            detail="인증번호 입력 가능 횟수를 초과했습니다."
        )

    if result == "WRONG_CODE":
        raise HTTPException(
            status_code=400,
            detail="인증번호가 올바르지 않습니다."
        )

    return {
        "message": "이메일 인증이 완료되었습니다."
    }