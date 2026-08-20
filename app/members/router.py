from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.service import (
    save_refresh_token,
    revoke_refresh_token,
    get_refresh_token_record,
    revoke_all_user_tokens
)

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)

from app.auth.dependencies import get_current_user_id

from app.database.connection import get_db

from app.members.schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    TokenRefresh,
    PasswordChange,
    MemberDelete
)

from app.members.service import (
    create_user,
    get_user,
    update_user,
    delete_user,
    login_user,
    change_password
)



router = APIRouter()


# ========================================
# 회원가입
# ========================================

@router.post(
    "/members",
    response_model=UserResponse
)
def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # 회원가입 처리
    new_user = create_user(
        db,
        user.email,
        user.name,
        user.password
    )

    # 이메일 중복
    if new_user is None:
        raise HTTPException(
            status_code=409,
            detail="이미 가입된 이메일입니다."
        )

    return new_user


# ========================================
# 로그인
# ========================================

@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    # 이메일과 비밀번호 확인
    login_user_result = login_user(
        db,
        user.email,
        user.password
    )

    if login_user_result is None:
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # Access Token 생성
    access_token = create_access_token(
    login_user_result.id,
    login_user_result.token_version
)

    # Refresh Token 생성
    refresh_token, jti, expires_at = create_refresh_token(
        login_user_result.id
    )

    # Refresh Token 정보를 DB에 저장
    save_refresh_token(
        db,
        login_user_result.id,
        jti,
        expires_at
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# Access Token 재발급
@router.post("/refresh")
def refresh_access_token(
    token: TokenRefresh,
    db: Session = Depends(get_db)
):
    # 1. JWT 자체 검증
    user_id, jti = verify_refresh_token(
        token.refresh_token
    )

    # 2. DB에서 Refresh Token 조회
    token_record = get_refresh_token_record(
        db,
        jti
    )

    # DB에 존재하지 않는 토큰
    if token_record is None:
        raise HTTPException(
            status_code=401,
            detail="존재하지 않는 Refresh Token입니다."
        )

    # 3. 이미 폐기된 토큰이 다시 사용된 경우
    if token_record.revoked_at is not None:

        # 토큰 탈취 가능성이 있으므로
        # 해당 사용자의 모든 Refresh Token 폐기
        revoke_all_user_tokens(
            db,
            user_id
        )

        raise HTTPException(
            status_code=401,
            detail=(
                "이미 사용된 Refresh Token이 다시 감지되었습니다. "
                "모든 로그인 세션이 종료되었습니다."
            )
        )

    # 4. 기존 Refresh Token 폐기
    revoke_refresh_token(
        db,
        jti
    )

    # 5. 새로운 Access Token 생성
        # 현재 회원 조회
    user = get_user(
        db,
        user_id
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="회원을 찾을 수 없습니다."
        )

    # 현재 token_version으로 새 Access Token 생성
    new_access_token = create_access_token(
        user.id,
        user.token_version
    )

    # 6. 새로운 Refresh Token 생성
    new_refresh_token, new_jti, expires_at = (
        create_refresh_token(user_id)
    )

    # 7. 새 Refresh Token DB 저장
    save_refresh_token(
        db,
        user_id,
        new_jti,
        expires_at
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# 로그아웃
@router.post("/logout")
def logout(
    token: TokenRefresh,
    db: Session = Depends(get_db)
):
    # Refresh Token 자체 검증
    # user_id는 사용하지 않으므로 _ 로 받는다.
    _, jti = verify_refresh_token(
        token.refresh_token
    )

    # DB에서 Refresh Token 폐기
    revoked = revoke_refresh_token(
        db,
        jti
    )

    if not revoked:
        raise HTTPException(
            status_code=401,
            detail="이미 폐기되었거나 존재하지 않는 Refresh Token입니다."
        )

    return {
        "message": "로그아웃되었습니다."
    }


# 내 회원정보 조회
@router.get(
    "/members/me",
    response_model=UserResponse
)
def get_my_member(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # JWT에서 가져온 현재 로그인 사용자 ID로 회원 조회
    user = get_user(
        db,
        current_user_id
    )

    # 회원이 존재하지 않는 경우
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다."
        )

    return user


# 내 회원정보 수정
@router.patch(
    "/members/me",
    response_model=UserResponse
)
def update_my_member(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    result = update_user(
        db,
        current_user_id,
        user.email,
        user.name
    )

    # 회원이 존재하지 않는 경우
    if result == "USER_NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다."
        )

    # 이미 사용 중인 이메일
    if result == "EMAIL_ALREADY_EXISTS":
        raise HTTPException(
            status_code=409,
            detail="이미 사용 중인 이메일입니다."
        )

    return result


# 회원 탈퇴
@router.delete("/members/me")
def delete_my_member(
    delete_data: MemberDelete,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # 현재 비밀번호를 확인한 후 Soft Delete
    result = delete_user(
        db,
        current_user_id,
        delete_data.current_password
    )

    # 회원이 존재하지 않는 경우
    if result == "USER_NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다."
        )

    # 현재 비밀번호가 틀린 경우
    if result == "WRONG_PASSWORD":
        raise HTTPException(
            status_code=401,
            detail="현재 비밀번호가 올바르지 않습니다."
        )

    # 해당 사용자의 모든 Refresh Token 폐기
    revoke_all_user_tokens(
        db,
        current_user_id
    )

    return {
        "message": "회원 탈퇴가 처리되었습니다."
    }



@router.patch("/members/me/password")
def change_my_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # 비밀번호 변경
    result = change_password(
        db,
        current_user_id,
        password_data.current_password,
        password_data.new_password
    )

    # 회원 없음
    if result == "USER_NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="회원을 찾을 수 없습니다."
        )

    # 현재 비밀번호 불일치
    if result == "WRONG_PASSWORD":
        raise HTTPException(
            status_code=401,
            detail="현재 비밀번호가 올바르지 않습니다."
        )

    # 기존 비밀번호와 동일
    if result == "SAME_PASSWORD":
        raise HTTPException(
            status_code=400,
            detail="새 비밀번호는 기존 비밀번호와 달라야 합니다."
        )

    # 비밀번호가 변경되었으므로
    # 모든 Refresh Token 폐기
    revoke_all_user_tokens(
        db,
        current_user_id
    )

    return {
        "message": "비밀번호가 변경되었습니다. 다시 로그인해주세요."
    }