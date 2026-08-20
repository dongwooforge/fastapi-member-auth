from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.members.model import Member
from datetime import datetime

# 이메일로 회원을 조회한다.
def find_member_by_email(
    db: Session,
    email: str
):
    # 탈퇴하지 않은 회원만 조회
    return (
        db.query(Member)
        .filter(
            Member.email == email,
            Member.deleted_at.is_(None)
        )
        .first()
    )


# ID로 회원을 조회한다.
def find_member_by_id(
    db: Session,
    user_id: int
):
    # 탈퇴하지 않은 회원만 조회
    return (
        db.query(Member)
        .filter(
            Member.id == user_id,
            Member.deleted_at.is_(None)
        )
        .first()
    )


# 회원을 생성한다.
def create_member(
    db: Session,
    email: str,
    name: str,
    password: str
):
    member = Member(
        email=email,
        name=name,
        password=password
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


# 회원 정보를 수정한다.
def update_member(
    db: Session,
    member: Member
):
    # 탈퇴한 회원은 수정할 수 없다.
    if member.deleted_at is not None:
        return None

    try:
        db.commit()
        db.refresh(member)

        return member

    except IntegrityError:
        db.rollback()
        raise

# 회원을 삭제한다.
def soft_delete_member(
    db: Session,
    member: Member
):
    # 실제 row를 삭제하지 않고 탈퇴 시간만 기록
    member.deleted_at = datetime.now()

    # 기존 Access Token 전체 무효화
    member.token_version += 1

    db.commit()
    db.refresh(member)

    return member