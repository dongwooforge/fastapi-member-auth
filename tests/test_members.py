from tests.helpers import verify_email


# ========================================
# 회원가입 성공
# ========================================

def test_signup(client):
    email = "signup@test.com"

    # 이메일 인증
    verify_email(
        client,
        email
    )

    # 회원가입
    response = client.post(
        "/members",
        json={
            "email": email,
            "name": "홍길동",
            "password": "Abcd1234!"
        }
    )

    assert response.status_code == 200

    data = response.json()

    # 응답 내용 확인
    assert data["email"] == email
    assert data["name"] == "홍길동"

    # 비밀번호가 응답에 노출되지 않는지 확인
    assert "password" not in data


# ========================================
# 이메일 미인증 회원가입 차단
# ========================================

def test_signup_without_email_verification(
    client
):
    response = client.post(
        "/members",
        json={
            "email": "notverified@test.com",
            "name": "홍길동",
            "password": "Abcd1234!"
        }
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "이메일 인증이 필요합니다."
    )


# ========================================
# 이메일 중복 회원가입 차단
# ========================================

def test_signup_duplicate_email(client):
    email = "duplicate@test.com"

    # 이메일 인증
    verify_email(
        client,
        email
    )

    # 첫 번째 회원가입
    first_response = client.post(
        "/members",
        json={
            "email": email,
            "name": "회원1",
            "password": "Abcd1234!"
        }
    )

    assert first_response.status_code == 200

    # 동일한 이메일로 다시 회원가입
    response = client.post(
        "/members",
        json={
            "email": email,
            "name": "회원2",
            "password": "Abcd1234!"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "이미 가입된 이메일입니다."
    )


# ========================================
# 잘못된 이메일 형식
# ========================================

def test_signup_invalid_email(client):
    response = client.post(
        "/members",
        json={
            "email": "not-email",
            "name": "테스트회원",
            "password": "Abcd1234!"
        }
    )

    assert response.status_code == 422


# ========================================
# 비밀번호 정책 위반
# ========================================

def test_signup_invalid_password(client):
    response = client.post(
        "/members",
        json={
            "email": "password@test.com",
            "name": "테스트회원",
            "password": "abcd1234"
        }
    )

    assert response.status_code == 422