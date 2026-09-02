def verify_email(client, email):
    # 인증번호 요청
    response = client.post(
        "/email-verifications",
        json={
            "email": email
        }
    )

    assert response.status_code == 200

    code = response.json()["verification_code"]

    # 인증번호 확인
    response = client.post(
        "/email-verifications/verify",
        json={
            "email": email,
            "code": code
        }
    )

    assert response.status_code == 200


def signup_user(
    client,
    email="auth@test.com",
    name="인증테스트",
    password="Abcd1234!"
):
    # 이메일 인증부터 수행
    verify_email(
        client,
        email
    )

    # 인증된 이메일로 회원가입
    return client.post(
        "/members",
        json={
            "email": email,
            "name": name,
            "password": password
        }
    )