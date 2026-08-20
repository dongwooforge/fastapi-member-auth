from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    token_version: Mapped[int] = mapped_column(
        default=1,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    # 탈퇴하지 않은 회원은 NULL
    # 탈퇴한 회원은 탈퇴 시간이 기록된다.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="member"
    )