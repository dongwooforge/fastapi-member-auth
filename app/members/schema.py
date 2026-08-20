from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    # 이메일 형식 검증
    email: EmailStr

    # 이름
    name: str

    # 비밀번호
    password: str = Field(min_length=8)

    # 비밀번호 조건 검증
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:

        # 영문 대문자 확인
        if not any(char.isupper() for char in value):
            raise ValueError(
                "비밀번호에는 영문 대문자가 포함되어야 합니다."
            )

        # 영문 소문자 확인
        if not any(char.islower() for char in value):
            raise ValueError(
                "비밀번호에는 영문 소문자가 포함되어야 합니다."
            )

        # 숫자 확인
        if not any(char.isdigit() for char in value):
            raise ValueError(
                "비밀번호에는 숫자가 포함되어야 합니다."
            )

        # 특수문자 확인
        if not any(
            not char.isalnum() and not char.isspace()
            for char in value
        ):
            raise ValueError(
                "비밀번호에는 특수문자가 포함되어야 합니다."
            )

        # 공백 확인
        if any(char.isspace() for char in value):
            raise ValueError(
                "비밀번호에는 공백을 사용할 수 없습니다."
            )

        # 영문/숫자/특수문자 외 문자 확인
        if not all(
            char.isascii()
            for char in value
        ):
            raise ValueError(
                "비밀번호에는 영문, 숫자, 특수문자만 사용할 수 있습니다."
            )

        return value


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

    password: str | None = Field(
        default=None,
        min_length=8
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:

        # 비밀번호를 수정하지 않는 경우
        if value is None:
            return value

        # 영문 대문자
        if not any(char.isupper() for char in value):
            raise ValueError(
                "비밀번호에는 영문 대문자가 포함되어야 합니다."
            )

        # 영문 소문자
        if not any(char.islower() for char in value):
            raise ValueError(
                "비밀번호에는 영문 소문자가 포함되어야 합니다."
            )

        # 숫자
        if not any(char.isdigit() for char in value):
            raise ValueError(
                "비밀번호에는 숫자가 포함되어야 합니다."
            )

        # 특수문자
        if not any(
            not char.isalnum() and not char.isspace()
            for char in value
        ):
            raise ValueError(
                "비밀번호에는 특수문자가 포함되어야 합니다."
            )

        # 공백
        if any(char.isspace() for char in value):
            raise ValueError(
                "비밀번호에는 공백을 사용할 수 없습니다."
            )

        # 영문/숫자/특수문자 외 문자
        if not all(char.isascii() for char in value):
            raise ValueError(
                "비밀번호에는 영문, 숫자, 특수문자만 사용할 수 있습니다."
            )

        return value


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class UserLogin(BaseModel):
    # 로그인 이메일
    email: EmailStr

    # 로그인 비밀번호
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    # 현재 비밀번호
    current_password: str

    # 새 비밀번호
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        # 영문 대문자
        if not any(char.isupper() for char in value):
            raise ValueError(
                "비밀번호에는 영문 대문자가 포함되어야 합니다."
            )

        # 영문 소문자
        if not any(char.islower() for char in value):
            raise ValueError(
                "비밀번호에는 영문 소문자가 포함되어야 합니다."
            )

        # 숫자
        if not any(char.isdigit() for char in value):
            raise ValueError(
                "비밀번호에는 숫자가 포함되어야 합니다."
            )

        # 특수문자
        if not any(
            not char.isalnum() and not char.isspace()
            for char in value
        ):
            raise ValueError(
                "비밀번호에는 특수문자가 포함되어야 합니다."
            )

        # 공백 금지
        if any(char.isspace() for char in value):
            raise ValueError(
                "비밀번호에는 공백을 사용할 수 없습니다."
            )

        # ASCII만 허용 → 한글 등 제외
        if not all(char.isascii() for char in value):
            raise ValueError(
                "비밀번호에는 영문, 숫자, 특수문자만 사용할 수 있습니다."
            )

        return value

#회원삭제 시 패스워드 필요
class MemberDelete(BaseModel):
    current_password: str