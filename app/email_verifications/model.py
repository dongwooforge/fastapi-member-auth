from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    # 인증 대상 이메일
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # 인증번호 원문이 아닌 Hash 값 저장
    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 인증번호 만료 시각
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    # 인증 성공 시각
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # 잘못된 인증번호 입력 횟수
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 인증 요청 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )