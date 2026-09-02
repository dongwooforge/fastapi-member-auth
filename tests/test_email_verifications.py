def test_request_email_verification(client):
    response = client.post(
        "/email-verifications",
        json={
            "email": "verify@test.com"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "인증번호가 생성되었습니다."
    assert "verification_code" in data
    assert len(data["verification_code"]) == 6
    assert data["verification_code"].isdigit()


def test_verify_email_success(client):
    # 인증번호 발급
    request_response = client.post(
        "/email-verifications",
        json={
            "email": "success@test.com"
        }
    )

    code = request_response.json()[
        "verification_code"
    ]

    # 인증번호 확인
    response = client.post(
        "/email-verifications/verify",
        json={
            "email": "success@test.com",
            "code": code
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "이메일 인증이 완료되었습니다."
    }


def test_verify_email_wrong_code(client):
    client.post(
        "/email-verifications",
        json={
            "email": "wrong@test.com"
        }
    )

    response = client.post(
        "/email-verifications/verify",
        json={
            "email": "wrong@test.com",
            "code": "999999"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "인증번호가 올바르지 않습니다."
    )


def test_verify_email_not_found(client):
    response = client.post(
        "/email-verifications/verify",
        json={
            "email": "nothing@test.com",
            "code": "123456"
        }
    )

    assert response.status_code == 404


def test_verification_code_cannot_be_reused(client):
    request_response = client.post(
        "/email-verifications",
        json={
            "email": "reuse@test.com"
        }
    )

    code = request_response.json()[
        "verification_code"
    ]

    # 첫 번째 인증
    first_response = client.post(
        "/email-verifications/verify",
        json={
            "email": "reuse@test.com",
            "code": code
        }
    )

    assert first_response.status_code == 200

    # 같은 인증번호 재사용
    second_response = client.post(
        "/email-verifications/verify",
        json={
            "email": "reuse@test.com",
            "code": code
        }
    )

    assert second_response.status_code == 409


def test_verification_too_many_attempts(client):
    client.post(
        "/email-verifications",
        json={
            "email": "attempt@test.com"
        }
    )

    # 5회 잘못 입력
    for _ in range(5):
        response = client.post(
            "/email-verifications/verify",
            json={
                "email": "attempt@test.com",
                "code": "999999"
            }
        )

        assert response.status_code == 400

    # 6번째 시도
    response = client.post(
        "/email-verifications/verify",
        json={
            "email": "attempt@test.com",
            "code": "999999"
        }
    )

    assert response.status_code == 429


from datetime import datetime, timedelta

from app.email_verifications.model import EmailVerification


def test_verification_code_expired(
    client,
    db
):
    # 인증번호 발급
    request_response = client.post(
        "/email-verifications",
        json={
            "email": "expired@test.com"
        }
    )

    code = request_response.json()[
        "verification_code"
    ]

    # DB에서 해당 인증 요청 조회
    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email
            == "expired@test.com"
        )
        .order_by(
            EmailVerification.created_at.desc()
        )
        .first()
    )

    # 만료시간을 강제로 과거로 변경
    verification.expires_at = (
        datetime.now() - timedelta(minutes=1)
    )

    db.commit()

    # 만료된 인증번호로 인증 시도
    response = client.post(
        "/email-verifications/verify",
        json={
            "email": "expired@test.com",
            "code": code
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "인증번호가 만료되었습니다."
    )