def test_signup(client):
    # 회원가입 요청
    response = client.post(
        "/members",
        json={
            "email": "test@test.com",
            "name": "테스트회원",
            "password": "Abcd1234!"
        }
    )

    # HTTP 상태코드 확인
    assert response.status_code == 200

    data = response.json()

    # 응답 내용 확인
    assert data["email"] == "test@test.com"
    assert data["name"] == "테스트회원"

    # 비밀번호가 응답에 노출되지 않는지 확인
    assert "password" not in data



def test_signup_duplicate_email(client):
    # 첫 번째 회원가입
    client.post(
        "/members",
        json={
            "email": "test@test.com",
            "name": "회원1",
            "password": "Abcd1234!"
        }
    )

    # 동일한 이메일로 다시 회원가입
    response = client.post(
        "/members",
        json={
            "email": "test@test.com",
            "name": "회원2",
            "password": "Abcd1234!"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "이미 가입된 이메일입니다."


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


def test_signup_invalid_password(client):
    response = client.post(
        "/members",
        json={
            "email": "test@test.com",
            "name": "테스트회원",
            "password": "abcd1234"
        }
    )

    assert response.status_code == 422