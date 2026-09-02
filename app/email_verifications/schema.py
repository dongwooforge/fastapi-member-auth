from pydantic import BaseModel, EmailStr


# 이메일 인증번호 요청
class EmailVerificationRequest(BaseModel):
    email: EmailStr


# 이메일 인증번호 확인
class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: str