from app.members.model import Member

def signup_user(client):
    return client.post(
        "/members",
        json={
            "email": "auth@test.com",
            "name": "인증테스트",
            "password": "Abcd1234!"
        }
    )


def login_user(client):
    return client.post(
        "/login",
        json={
            "email": "auth@test.com",
            "password": "Abcd1234!"
        }
    )


def test_login_success(client):
    signup_user(client)

    response = login_user(client)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    signup_user(client)

    response = client.post(
        "/login",
        json={
            "email": "auth@test.com",
            "password": "Wrong1234!"
        }
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "이메일 또는 비밀번호가 올바르지 않습니다."
    )


def test_get_my_member_with_token(client):
    signup_user(client)

    login_response = login_user(client)

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "auth@test.com"
    assert data["name"] == "인증테스트"


def test_get_my_member_without_token(client):
    signup_user(client)

    response = client.get(
        "/members/me"
    )

    assert response.status_code == 401



def test_refresh_token_rotation_and_reuse_detection(client):
    # 1. 회원가입
    signup_user(client)

    # 2. 로그인
    login_response = login_user(client)

    assert login_response.status_code == 200

    login_data = login_response.json()

    refresh_token_a = login_data["refresh_token"]

    # 3. Refresh A를 사용해 새 토큰 발급
    refresh_response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token_a
        }
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    # 새로운 Access / Refresh Token이 발급되어야 한다.
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data

    refresh_token_b = refresh_data["refresh_token"]

    # Rotation이므로 A와 B는 달라야 한다.
    assert refresh_token_a != refresh_token_b

    # 4. 이미 사용된 Refresh A를 다시 사용
    reuse_response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token_a
        }
    )

    # 재사용 탐지
    assert reuse_response.status_code == 401

    assert (
        reuse_response.json()["detail"]
        == "이미 사용된 Refresh Token이 다시 감지되었습니다. "
           "모든 로그인 세션이 종료되었습니다."
    )

    # 5. Refresh A 재사용이 감지되었으므로
    # 새로 발급받았던 Refresh B도 폐기되어야 한다.
    refresh_b_response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token_b
        }
    )

    assert refresh_b_response.status_code == 401



def test_refresh_token_rotation(client):
    # 회원가입
    signup_user(client)

    # 로그인
    login_response = login_user(client)

    refresh_token_a = login_response.json()["refresh_token"]

    # 첫 번째 Refresh
    response_a = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token_a
        }
    )

    assert response_a.status_code == 200

    data_a = response_a.json()

    refresh_token_b = data_a["refresh_token"]

    # 새 Refresh Token이 발급됐는지 확인
    assert refresh_token_a != refresh_token_b

    # 새 Refresh Token은 정상적으로 사용할 수 있어야 한다.
    response_b = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token_b
        }
    )

    assert response_b.status_code == 200

    refresh_token_c = response_b.json()["refresh_token"]

    # B 역시 Rotation되어 새로운 C가 발급
    assert refresh_token_b != refresh_token_c


def test_logout_revokes_refresh_token(client):
    # 회원가입 + 로그인
    signup_user(client)

    login_response = login_user(client)

    refresh_token = login_response.json()["refresh_token"]

    # 로그아웃
    logout_response = client.post(
        "/logout",
        json={
            "refresh_token": refresh_token
        }
    )

    assert logout_response.status_code == 200

    assert (
        logout_response.json()["message"]
        == "로그아웃되었습니다."
    )

    # 로그아웃한 Refresh Token 재사용
    refresh_response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh_response.status_code == 401



def test_password_change_invalidates_old_access_token(client):
    # 1. 회원가입
    signup_user(client)

    # 2. 로그인
    login_response = login_user(client)

    assert login_response.status_code == 200

    login_data = login_response.json()

    old_access_token = login_data["access_token"]
    old_refresh_token = login_data["refresh_token"]

    # 3. 기존 Access Token으로 내 정보 조회
    me_response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {old_access_token}"
        }
    )

    assert me_response.status_code == 200

    # 4. 비밀번호 변경
    password_change_response = client.patch(
        "/members/me/password",
        json={
            "current_password": "Abcd1234!",
            "new_password": "NewPass123!"
        },
        headers={
            "Authorization": f"Bearer {old_access_token}"
        }
    )

    assert password_change_response.status_code == 200

    assert (
        password_change_response.json()["message"]
        == "비밀번호가 변경되었습니다. 다시 로그인해주세요."
    )

    # 5. 비밀번호 변경 전에 발급받은 Access Token 재사용
    old_access_response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {old_access_token}"
        }
    )

    # token_version이 변경됐으므로 거부되어야 한다.
    assert old_access_response.status_code == 401

    assert (
        old_access_response.json()["detail"]
        == "만료된 로그인 정보입니다. 다시 로그인해주세요."
    )

    # 6. 기존 Refresh Token도 폐기되었는지 확인
    old_refresh_response = client.post(
        "/refresh",
        json={
            "refresh_token": old_refresh_token
        }
    )

    assert old_refresh_response.status_code == 401

    # 7. 기존 비밀번호로 로그인 시도
    old_password_login = client.post(
        "/login",
        json={
            "email": "auth@test.com",
            "password": "Abcd1234!"
        }
    )

    assert old_password_login.status_code == 401

    # 8. 새 비밀번호로 로그인
    new_password_login = client.post(
        "/login",
        json={
            "email": "auth@test.com",
            "password": "NewPass123!"
        }
    )

    assert new_password_login.status_code == 200

    new_access_token = new_password_login.json()["access_token"]

    # 9. 새 Access Token은 정상 사용 가능
    new_access_response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {new_access_token}"
        }
    )

    assert new_access_response.status_code == 200


def test_soft_delete_member(client, db):
    # 1. 회원가입
    signup_user(client)

    # 2. 로그인
    login_response = login_user(client)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # 3. 회원 탈퇴
    delete_response = client.request(
        "DELETE",
        "/members/me",
        json={
            "current_password": "Abcd1234!"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert delete_response.status_code == 200
    assert (
        delete_response.json()["message"]
        == "회원 탈퇴가 처리되었습니다."
    )

    # 4. 기존 Access Token은 사용할 수 없어야 한다.
    old_access_response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert old_access_response.status_code == 401

    # 5. 기존 Refresh Token도 사용할 수 없어야 한다.
    old_refresh_response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert old_refresh_response.status_code == 401

    # 6. 탈퇴한 회원은 로그인할 수 없어야 한다.
    login_after_delete = client.post(
        "/login",
        json={
            "email": "auth@test.com",
            "password": "Abcd1234!"
        }
    )

    assert login_after_delete.status_code == 401

    # 7. DB row 자체는 삭제되지 않고 남아 있어야 한다.
    deleted_member = (
        db.query(Member)
        .filter(Member.email == "auth@test.com")
        .first()
    )

    assert deleted_member is not None

    # deleted_at에 탈퇴 시간이 기록되어 있어야 한다.
    assert deleted_member.deleted_at is not None

def test_soft_delete_wrong_password(client):
    signup_user(client)

    login_response = login_user(client)
    access_token = login_response.json()["access_token"]

    response = client.request(
        "DELETE",
        "/members/me",
        json={
            "current_password": "Wrong1234!"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "현재 비밀번호가 올바르지 않습니다."
    )

    # 탈퇴에 실패했으므로 기존 Access Token은 계속 유효해야 한다.
    me_response = client.get(
        "/members/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert me_response.status_code == 200


def test_deleted_member_cannot_update_profile(client):
    signup_user(client)

    login_response = login_user(client)

    access_token = login_response.json()["access_token"]

    # 회원 탈퇴
    delete_response = client.request(
        "DELETE",
        "/members/me",
        json={
            "current_password": "Abcd1234!"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert delete_response.status_code == 200

    # 탈퇴 전 Access Token으로 회원정보 수정 시도
    update_response = client.patch(
        "/members/me",
        json={
            "name": "수정시도"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    # 탈퇴하면서 token_version이 바뀌었기 때문에 거부되어야 한다.
    assert update_response.status_code == 401