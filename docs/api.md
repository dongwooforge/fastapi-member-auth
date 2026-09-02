# API Documentation

## 인증 방식

보호된 API는 Access Token이 필요하다.

### Authorization Header

```text
Authorization: Bearer <access_token>
```

---

## 1. 이메일 인증번호 요청

`POST /email-verifications`

### 권한

없음

### Request Body

```json
{
  "email": "test@test.com"
}
```

### Response 200

현재 개발 단계에서는 테스트를 위해 인증번호를 응답에 포함합니다.

```json
{
  "message": "인증번호가 생성되었습니다.",
  "verification_code": "482193"
}
```

> 실제 이메일 발송 기능을 연결한 이후에는 `verification_code`를 API 응답에서 제거해야 합니다.

### 동작

- 6자리 인증번호 생성
- 인증번호 Hash 저장
- 인증번호 유효시간 5분
- 최대 인증 시도 횟수 5회

### Error

**422 Unprocessable Entity**
- 이메일 형식 오류

---

## 2. 이메일 인증번호 확인

`POST /email-verifications/verify`

### 권한

없음

### Request Body

```json
{
  "email": "test@test.com",
  "code": "482193"
}
```

### Response 200

```json
{
  "message": "이메일 인증이 완료되었습니다."
}
```

### 동작

인증 성공 시 해당 인증 기록의 `verified_at`에 인증 완료 시각을 기록합니다.

인증이 완료된 이메일만 회원가입에 사용할 수 있습니다.

### Error

**400 Bad Request**
- 인증번호 불일치
- 인증번호 만료

**404 Not Found**
- 이메일 인증 요청이 존재하지 않음

**409 Conflict**
- 이미 인증 완료된 인증번호

**429 Too Many Requests**
- 인증번호 입력 가능 횟수 초과



## 3. 회원가입

`POST /members`

### 사전 조건

이메일 인증 완료 필요

회원가입에 사용할 이메일은 먼저 이메일 인증을 완료해야 합니다.

```text
POST /email-verifications
        ↓
POST /email-verifications/verify
        ↓
POST /members

### Request Body

```json
{
  "email": "test@test.com",
  "name": "홍길동",
  "password": "Abcd1234!"
}
```

### Response 200

```json
{
  "id": 1,
  "email": "test@test.com",
  "name": "홍길동"
}
```

### Error

**409 Conflict**
- 이미 가입된 이메일

**422 Unprocessable Entity**
- 이메일 형식 오류
- 비밀번호 정책 위반

---

## 4. 로그인

`POST /login`

### 권한

없음

### Request Body

```json
{
  "email": "test@test.com",
  "password": "Abcd1234!"
}
```

### Response 200

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### Error

**401 Unauthorized**
- 이메일 또는 비밀번호 불일치

---

## 5. 내 회원정보 조회

`GET /members/me`

### 권한

Access Token 필요

### Header

```text
Authorization: Bearer <access_token>
```

### Response 200

```json
{
  "id": 1,
  "email": "test@test.com",
  "name": "홍길동"
}
```

### Error

**401 Unauthorized**
- 토큰 없음
- 유효하지 않은 토큰
- token_version 불일치
- 탈퇴한 회원

---

## 6. 내 회원정보 수정

`PATCH /members/me`

### 권한

Access Token 필요

### Header

```text
Authorization: Bearer <access_token>
```

### Request Body

```json
{
  "email": "new@test.com",
  "name": "김철수"
}
```

모든 필드는 선택값이다.

### Response 200

```json
{
  "id": 1,
  "email": "new@test.com",
  "name": "김철수"
}
```

### Error

**401 Unauthorized**
- 인증 실패

**409 Conflict**
- 이미 사용 중인 이메일

**422 Unprocessable Entity**
- 이메일 형식 오류

---

## 7. 비밀번호 변경

`PATCH /members/me/password`

### 권한

Access Token 필요

### Header

```text
Authorization: Bearer <access_token>
```

### Request Body

```json
{
  "current_password": "Abcd1234!",
  "new_password": "NewPass123!"
}
```

### Response 200

```json
{
  "message": "비밀번호가 변경되었습니다. 다시 로그인해주세요."
}
```

### 보안 처리

비밀번호 변경 성공 시:

- `token_version` 증가
- 기존 Access Token 무효화
- 모든 Refresh Token 폐기
- 재로그인 필요

### Error

**400 Bad Request**
- 새 비밀번호가 기존 비밀번호와 동일

**401 Unauthorized**
- 인증 실패
- 현재 비밀번호 불일치

**422 Unprocessable Entity**
- 새 비밀번호가 비밀번호 정책을 충족하지 않음

---

## 8. Access Token 재발급

`POST /refresh`

### 권한

Refresh Token 필요

### Request Body

```json
{
  "refresh_token": "..."
}
```

### Response 200

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### 동작

Refresh Token Rotation을 사용한다.

```text
Refresh Token A 사용
        ↓
Refresh Token A 폐기
        ↓
새 Access Token 발급
        +
Refresh Token B 발급
```

이미 사용된 Refresh Token이 다시 사용되면 재사용 공격 가능성이 있다고 판단하여 해당 사용자의 모든 Refresh Token을 폐기한다.

### Error

**401 Unauthorized**
- 유효하지 않은 Refresh Token
- 존재하지 않는 Refresh Token
- 이미 폐기된 Refresh Token
- Refresh Token 재사용 감지

---

## 9. 로그아웃

`POST /logout`

### 권한

유효한 Refresh Token 필요

### Request Body

```json
{
  "refresh_token": "..."
}
```

### Response 200

```json
{
  "message": "로그아웃되었습니다."
}
```

### 동작

전달된 Refresh Token을 폐기한다.

### Error

**401 Unauthorized**
- 유효하지 않은 Refresh Token
- 이미 폐기된 Refresh Token
- 존재하지 않는 Refresh Token

---

## 10. 회원 탈퇴

`DELETE /members/me`

### 권한

Access Token 필요

### Header

```text
Authorization: Bearer <access_token>
```

### Request Body

```json
{
  "current_password": "Abcd1234!"
}
```

### Response 200

```json
{
  "message": "회원 탈퇴가 처리되었습니다."
}
```

### 동작

회원 데이터는 즉시 물리적으로 삭제하지 않고 Soft Delete 방식으로 처리한다.

회원 탈퇴 성공 시:

- `members` row 유지
- `deleted_at`에 탈퇴 시각 기록
- `token_version` 증가
- 기존 Access Token 무효화
- 모든 Refresh Token 폐기
- 이후 로그인 차단
- 회원정보 조회 및 수정 차단

### Error

**401 Unauthorized**
- 인증 실패
- 현재 비밀번호 불일치