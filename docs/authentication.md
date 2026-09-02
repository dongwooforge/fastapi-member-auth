# Authentication

이 문서는 FastAPI Member Auth 프로젝트의 인증 및 세션 관리 구조를 설명합니다.

본 프로젝트는 JWT 기반의 Access Token과 Refresh Token을 사용하며,
Refresh Token은 데이터베이스에서 상태를 관리합니다.


## 이메일 인증

회원가입 전에 이메일 소유권 확인을 위해 이메일 인증을 수행합니다.

```text
이메일 입력
    ↓
인증번호 요청
    ↓
6자리 인증번호 생성
    ↓
인증번호 Hash 저장
    ↓
인증번호 확인
    ↓
verified_at 기록
    ↓
회원가입 허용
```

### 인증번호

인증번호는 6자리 숫자로 생성합니다.

```text
예: 482193
```

인증번호 원문은 데이터베이스에 저장하지 않고 Hash 값으로 저장합니다.

```text
482193
   ↓
Hash
   ↓
code_hash
```

현재 인증번호의 유효시간은 5분이며 최대 5회의 인증 시도를 허용합니다.

### 회원가입과 이메일 인증

`POST /members` 요청 시 서버는 해당 이메일에 유효한 인증 완료 기록이 존재하는지 확인합니다.

```text
POST /members
      ↓
이메일 인증 기록 조회
      ↓
verified_at 존재?
      +
expires_at이 지나지 않았는가?
      ↓
     YES
      ↓
회원가입 진행
```

유효한 인증 기록이 존재하지 않으면 회원가입을 거부합니다.

```text
403 Forbidden
```

이메일 인증은 사용자의 실명이나 실제 신원을 확인하는 본인확인이 아니라,
해당 이메일 주소에 접근할 수 있는 사용자인지를 확인하기 위한 절차입니다.


---

## 1. 인증 구조

로그인에 성공하면 서버는 두 종류의 토큰을 발급합니다.

- Access Token
- Refresh Token

```text
Email + Password
       ↓
사용자 인증
       ↓
┌─────────────────┐
│   FastAPI API   │
└────────┬────────┘
         ↓
┌────────┴────────┐
│                 │
Access Token   Refresh Token
│                 │
API 인증       Access Token 재발급
```

두 토큰은 역할과 관리 방법이 다릅니다.

---

## 2. Access Token

Access Token은 보호된 API에 접근할 때 사용합니다.

클라이언트는 다음과 같이 HTTP Authorization Header에 Access Token을 전달합니다.

```text
Authorization: Bearer <access_token>
```

예:

```text
GET /members/me
Authorization: Bearer eyJ...
```

서버는 Access Token을 검증한 후 현재 로그인한 회원을 식별합니다.

---

## 3. Access Token 검증

보호된 API에 요청이 들어오면 다음 순서로 인증을 수행합니다.

```text
Authorization Header
        ↓
Bearer Token 추출
        ↓
JWT 서명 및 만료시간 검증
        ↓
user_id 추출
        ↓
회원 조회
        ↓
token_version 검증
        ↓
인증 성공
```

검증에 실패하면 보호된 API에 접근할 수 없습니다.

---

## 4. token_version

JWT는 한 번 발급하면 일반적으로 만료될 때까지 자체적으로 유효합니다.

하지만 비밀번호 변경이나 회원 탈퇴처럼 기존 Access Token을 즉시 사용할 수 없게 만들어야 하는 상황이 있습니다.

이를 위해 회원 테이블에 `token_version`을 저장합니다.

예:

```text
Database

member.id = 1
token_version = 3
```

Access Token에도 발급 당시의 `token_version`을 포함합니다.

```text
Access Token

user_id = 1
token_version = 3
```

API 요청 시 두 값을 비교합니다.

```text
JWT token_version == DB token_version
              ↓
             정상
```

값이 다르면 기존 Access Token으로 판단하고 인증을 거부합니다.

```text
JWT token_version = 3
DB token_version  = 4

        ↓

401 Unauthorized
```

---

## 5. 비밀번호 변경과 Access Token 무효화

비밀번호가 변경되면 회원의 `token_version`을 증가시킵니다.

```text
비밀번호 변경 전

DB token_version = 1
기존 Access Token = version 1

        ↓

비밀번호 변경

        ↓

DB token_version = 2
```

따라서 기존 Access Token에는 여전히 version 1이 들어 있으므로 이후 요청에서 거부됩니다.

```text
기존 Access Token
version = 1

DB
version = 2

1 != 2

→ 401 Unauthorized
```

비밀번호 변경 성공 시 모든 Refresh Token도 함께 폐기합니다.

따라서 사용자는 새로운 비밀번호로 다시 로그인해야 합니다.

---

## 6. Refresh Token

Refresh Token은 Access Token이 만료되었을 때 새로운 Access Token을 발급받기 위해 사용합니다.

본 프로젝트에서는 Refresh Token을 완전한 Stateless 방식으로 사용하지 않습니다.

Refresh Token의 식별자인 `jti`와 상태를 데이터베이스에 저장합니다.

이를 통해 서버에서 Refresh Token을 폐기하거나 재사용 여부를 확인할 수 있습니다.

---

## 7. jti

각 Refresh Token에는 고유한 `jti`가 존재합니다.

개념적으로:

```text
Refresh Token A
jti = abc123

Refresh Token B
jti = xyz789
```

처럼 각각 다른 식별자를 가집니다.

서버는 Refresh Token을 발급할 때 해당 `jti`를 데이터베이스에 저장합니다.

```text
Refresh Token
      │
      │ jti
      ↓
refresh_tokens table
```

이를 통해 특정 Refresh Token의 상태를 추적할 수 있습니다.

---

## 8. Refresh Token Rotation

본 프로젝트는 Refresh Token Rotation을 사용합니다.

Refresh Token은 Access Token 재발급에 한 번 사용되면 폐기하고 새로운 Refresh Token을 발급합니다.

```text
Refresh Token A
        ↓
     /refresh
        ↓
A 유효성 확인
        ↓
Refresh Token A 폐기
        ↓
┌────────────────────────┐
│ 새로운 Access Token    │
│ 새로운 Refresh Token B │
└────────────────────────┘
```

이후 클라이언트는 Refresh Token B를 사용해야 합니다.

Refresh Token A는 다시 사용할 수 없습니다.

---

## 9. Refresh Token 재사용 탐지

이미 사용되어 폐기된 Refresh Token이 다시 사용되는 경우 토큰 탈취 가능성이 있다고 판단합니다.

예:

```text
정상 사용자

Refresh A
   ↓
사용
   ↓
Refresh B 발급


공격자

탈취했던 Refresh A
   ↓
다시 사용
```

서버에서는 Refresh A가 이미 폐기된 상태라는 것을 데이터베이스를 통해 확인할 수 있습니다.

```text
Refresh A
revoked_at != NULL
```

재사용이 감지되면 해당 사용자의 모든 Refresh Token을 폐기합니다.

```text
폐기된 Refresh Token 재사용
          ↓
     Reuse Detection
          ↓
해당 회원의 모든 Refresh Token 폐기
          ↓
      재로그인 필요
```

---

## 10. 로그아웃

로그아웃 시 전달된 Refresh Token을 폐기합니다.

```text
POST /logout
     ↓
Refresh Token 검증
     ↓
jti 조회
     ↓
revoked_at 기록
```

폐기된 Refresh Token으로는 새로운 Access Token을 발급받을 수 없습니다.

Access Token은 별도로 서버에 저장하지 않습니다.

따라서 일반 로그아웃에서는 Refresh Token을 폐기하여 새로운 Access Token 발급을 차단합니다.

---

## 11. 비밀번호 변경

비밀번호 변경은 현재 로그인한 사용자의 Access Token 인증과 현재 비밀번호 확인을 모두 요구합니다.

```text
Access Token 인증
        +
현재 비밀번호 확인
        ↓
새 비밀번호 Hash 저장
        ↓
token_version 증가
        ↓
모든 Refresh Token 폐기
        ↓
재로그인 필요
```

이를 통해 비밀번호 변경 전에 발급된 인증수단을 사용할 수 없도록 처리합니다.

---

## 12. 회원 탈퇴

회원 탈퇴도 현재 Access Token과 현재 비밀번호 확인을 요구합니다.

탈퇴 성공 시:

```text
회원 탈퇴
   ↓
deleted_at 기록
   ↓
token_version 증가
   ↓
모든 Refresh Token 폐기
   ↓
기존 Access Token 사용 불가
   ↓
로그인 차단
```

회원 데이터는 즉시 물리적으로 삭제하지 않고 Soft Delete 방식으로 처리합니다.

---

## 13. 인증 실패

다음과 같은 경우 인증이 거부될 수 있습니다.

- Access Token이 없음
- JWT가 유효하지 않음
- Access Token이 만료됨
- 회원이 존재하지 않음
- 탈퇴한 회원
- `token_version` 불일치
- Refresh Token이 유효하지 않음
- Refresh Token이 DB에 존재하지 않음
- Refresh Token이 이미 폐기됨
- Refresh Token 재사용이 감지됨

인증 실패 시 일반적으로 `401 Unauthorized`를 반환합니다.

---

## 14. 인증 설계 요약

```text
                  Login
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
    Access Token        Refresh Token
          │                   │
          │                   ↓
          │              DB 상태 관리
          │                   │
          │              Rotation
          │                   │
          │            Reuse Detection
          │
          ↓
   Protected API
          │
          ↓
   token_version 확인
```

Access Token은 빠른 API 인증을 담당하고,
Refresh Token은 데이터베이스 상태 관리와 Rotation을 통해 세션을 관리합니다.

비밀번호 변경과 회원 탈퇴 시에는 `token_version`과 Refresh Token 폐기를 함께 사용하여 기존 인증 정보를 무효화합니다.