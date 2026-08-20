from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.members.security import hash_password, verify_password
from app.members import db


# 회원가입
def create_user(
    session: Session,
    email: str,
    name: str,
    password: str
):
    # 이메일 중복 확인
    existing_user = db.find_member_by_email(
        session,
        email
    )

    if existing_user is not None:
        return None

    # 비밀번호 해싱
    hashed_password = hash_password(password)

    # 해시된 비밀번호를 DB에 저장
    return db.create_member(
        session,
        email,
        name,
        hashed_password
    )


# 회원 조회
def get_user(
    session: Session,
    user_id: int
):
    return db.find_member_by_id(
        session,
        user_id
    )


# 회원 수정
def update_user(
    session: Session,
    user_id: int,
    email: str | None = None,
    name: str | None = None
):
    # 탈퇴 회원은 find_member_by_id에서 조회되지 않는다.
    user = db.find_member_by_id(
        session,
        user_id
    )

    if user is None:
        return "USER_NOT_FOUND"

    if email is not None:
        if email != user.email:
            existing_user = db.find_member_by_email(
                session,
                email
            )

            if existing_user is not None:
                return "EMAIL_ALREADY_EXISTS"

            user.email = email

    if name is not None:
        user.name = name

    try:
        updated_user = db.update_member(
            session,
            user
        )

    except IntegrityError:
        return "EMAIL_ALREADY_EXISTS"

    if updated_user is None:
        return "USER_NOT_FOUND"

    return updated_user


# 회원 삭제
def delete_user(
    session: Session,
    user_id: int,
    current_password: str
):
    # 현재 회원 조회
    user = db.find_member_by_id(
        session,
        user_id
    )

    if user is None:
        return "USER_NOT_FOUND"

    # 탈퇴 전 현재 비밀번호 재확인
    if not verify_password(
        current_password,
        user.password
    ):
        return "WRONG_PASSWORD"

    # Soft Delete
    db.soft_delete_member(
        session,
        user
    )

    return "SUCCESS"


# 로그인
def login_user(
    session: Session,
    email: str,
    password: str
):
    # 이메일로 회원 조회
    user = db.find_member_by_email(
        session,
        email
    )

    # 회원이 존재하지 않는 경우
    if user is None:
        return None

    # 입력한 비밀번호와 DB의 해시 비교
    password_valid = verify_password(
        password,
        user.password
    )

    if not password_valid:
        return None

    return user


# 비밀번호 변경
def change_password(
    session: Session,
    user_id: int,
    current_password: str,
    new_password: str
):
    # 현재 회원 조회
    user = db.find_member_by_id(
        session,
        user_id
    )

    if user is None:
        return "USER_NOT_FOUND"

    # 현재 비밀번호 확인
    if not verify_password(
        current_password,
        user.password
    ):
        return "WRONG_PASSWORD"

    # 현재 비밀번호와 새 비밀번호가 같은지 확인
    if verify_password(
        new_password,
        user.password
    ):
        return "SAME_PASSWORD"

    # 새 비밀번호 해싱
    user.password = hash_password(
        new_password
    )

    # 기존 Access Token을 모두 무효화하기 위해
    # token_version 증가
    user.token_version += 1

    # DB 저장
    db.update_member(
        session,
        user
    )

    return "SUCCESS"