# Database

이 문서는 FastAPI Member Auth 프로젝트의 데이터베이스 구조와 데이터 관리 방식을 설명합니다.

본 프로젝트는 MySQL을 사용하며 SQLAlchemy ORM을 통해 데이터베이스에 접근합니다.

---

## 1. Database 구성

개발 환경에서는 Docker를 통해 MySQL 8.4를 실행합니다.

```text
FastAPI
   │
   │ SQLAlchemy
   ↓
MySQL 8.4
   │
   ├── members
   │
   └── refresh_tokens
```

애플리케이션의 데이터베이스 연결 정보는 `.env`의 `DATABASE_URL`을 통해 관리합니다.

테스트에서는 실제 서비스용 데이터베이스와 분리된 별도의 Test Database를 사용합니다.

---

## 2. members 테이블

`members` 테이블은 서비스의 회원 정보를 저장합니다.

주요 데이터:

| Column | 설명 |
|---|---|
| `id` | 회원 고유 식별자 |
| `email` | 로그인 이메일 |
| `name` | 회원 이름 |
| `password` | Hash 처리된 비밀번호 |
| `token_version` | Access Token 무효화에 사용하는 버전 |
| `created_at` | 회원 생성 시각 |
| `deleted_at` | 회원 탈퇴 시각 |

`deleted_at`이 `NULL`이면 활성 회원입니다.

```text
deleted_at = NULL
→ 활성 회원
```

탈퇴한 회원은 탈퇴 시각이 기록됩니다.

```text
deleted_at = 2026-08-21 15:00:00
→ 탈퇴 회원
```

---

## 3. 회원 식별

회원은 `id`를 기준으로 식별합니다.

```text
member.id
```

이메일이나 이름이 아니라 데이터베이스의 회원 PK를 서비스 내부의 고유 식별자로 사용합니다.

JWT에서도 회원을 식별하기 위해 회원 ID를 사용합니다.

---

## 4. Email

`email`은 회원가입 및 로그인에 사용합니다.

회원가입 시 동일한 이메일이 존재하는지 확인합니다.

데이터베이스에서도 이메일 중복을 방지하기 위해 UNIQUE 제약을 사용합니다.

```text
email
→ UNIQUE
```

애플리케이션 레벨의 중복 검사와 데이터베이스 UNIQUE 제약을 함께 사용하여 중복 회원 생성을 방지합니다.

---

## 5. Password

비밀번호 원문은 데이터베이스에 저장하지 않습니다.

```text
사용자 Password
       ↓
Password Hash
       ↓
members.password
```

로그인 시에도 비밀번호 원문끼리 비교하지 않습니다.

```text
입력 Password
      +
DB Password Hash
      ↓
verify_password()
```

검증 결과를 통해 로그인 성공 여부를 판단합니다.

---

## 6. token_version

`token_version`은 이미 발급된 Access Token을 서버에서 무효화하기 위해 사용합니다.

회원의 현재 버전:

```text
members.token_version = 2
```

Access Token 발급 당시 버전:

```text
JWT token_version = 2
```

두 값이 일치해야 인증에 성공합니다.

비밀번호 변경이나 회원 탈퇴처럼 기존 Access Token을 모두 무효화해야 하는 상황에서는 DB의 `token_version`을 증가시킵니다.

---

## 7. Soft Delete

회원 탈퇴 시 `DELETE FROM members`를 실행하지 않습니다.

대신:

```text
members.deleted_at
```

에 탈퇴 시간을 기록합니다.

```text
회원 탈퇴 전

deleted_at = NULL

       ↓

회원 탈퇴

       ↓

deleted_at = 탈퇴 시각
```

일반 회원 조회에서는:

```text
deleted_at IS NULL
```

조건을 사용하여 활성 회원만 조회합니다.

따라서 탈퇴 회원의 row는 데이터베이스에 존재하지만 일반 서비스 로직에서는 조회되지 않습니다.

---

## 8. refresh_tokens 테이블

Refresh Token은 JWT 자체만으로 관리하지 않고 데이터베이스에서도 상태를 관리합니다.

Refresh Token 전체 문자열을 저장하는 대신 토큰을 식별할 수 있는 `jti`를 관리합니다.

주요 데이터는 다음과 같은 역할을 가집니다.

| Column | 설명 |
|---|---|
| `id` | Refresh Token 레코드 PK |
| `user_id` | Refresh Token 소유 회원 |
| `jti` | Refresh Token 고유 식별자 |
| `expires_at` | Refresh Token 만료 시각 |
| `revoked_at` | Refresh Token 폐기 시각 |

`revoked_at`이 `NULL`이면 아직 폐기되지 않은 Refresh Token입니다.

```text
revoked_at = NULL
→ 사용 가능
```

폐기된 토큰:

```text
revoked_at != NULL
→ 사용 불가
```

---

## 9. members와 refresh_tokens 관계

한 명의 회원은 여러 Refresh Token을 가질 수 있습니다.

예를 들어 여러 기기에서 로그인할 수 있기 때문입니다.

```text
members

id = 1
   │
   ├──── refresh_token A
   ├──── refresh_token B
   └──── refresh_token C
```

따라서 관계는:

```text
Member 1 : N RefreshToken
```

입니다.

개념적으로:

```text
members
────────────────
id
1
2


refresh_tokens
────────────────────────────
id    user_id    jti
1       1        AAA
2       1        BBB
3       1        CCC
4       2        DDD
```

와 같은 구조가 됩니다.

---

## 10. Refresh Token 상태 관리

Refresh Token 발급 시:

```text
Refresh Token 생성
       ↓
jti 생성
       ↓
refresh_tokens INSERT
```

Refresh Token 사용 시:

```text
jti 조회
   ↓
존재 여부 확인
   ↓
revoked_at 확인
   ↓
기존 Token 폐기
   ↓
새 Refresh Token 저장
```

이를 통해 Refresh Token Rotation과 재사용 탐지가 가능합니다.

---

## 11. 모든 Refresh Token 폐기

비밀번호 변경이나 Refresh Token 재사용 탐지와 같이 모든 로그인 세션을 종료해야 하는 상황에서는 해당 회원의 활성 Refresh Token을 모두 폐기합니다.

개념적으로:

```text
user_id = 1

Refresh A → revoke
Refresh B → revoke
Refresh C → revoke
```

각 레코드를 물리적으로 삭제하는 대신 `revoked_at`을 기록하여 폐기 여부를 추적할 수 있습니다.

---

## 12. 데이터 접근 계층

회원 관련 데이터베이스 처리는 `app/members/db.py`에서 담당합니다.

```text
Router
  ↓
Service
  ↓
members/db.py
  ↓
SQLAlchemy
  ↓
MySQL
```

인증 관련 Refresh Token 데이터베이스 처리는 인증 모듈에서 담당합니다.

```text
Router
  ↓
Auth Service
  ↓
Auth DB
  ↓
SQLAlchemy
  ↓
MySQL
```

Router에서 직접 SQLAlchemy Query를 작성하지 않고 데이터 접근 로직을 분리하여 관리합니다.

---

## 13. Transaction 처리

회원정보 수정과 같이 데이터베이스 제약조건 위반 가능성이 있는 작업에서는 Transaction 실패 시 Rollback을 수행합니다.

예:

```text
UPDATE
   ↓
IntegrityError
   ↓
rollback()
   ↓
Transaction 정상 상태 복구
```

이를 통해 실패한 Transaction이 이후 데이터베이스 작업에 영향을 주는 것을 방지합니다.

---

## 14. Test Database

pytest 실행 시 실제 개발용 데이터베이스와 분리된 Test Database를 사용합니다.

```text
Application
    ↓
Development Database


pytest
    ↓
Test Database
```

이를 통해 테스트 과정에서 회원 생성, 수정, 삭제 또는 토큰 폐기 등이 실제 개발 데이터에 영향을 주지 않도록 합니다.

테스트는 다음 명령으로 실행합니다.

```bash
pytest -v
```

---

## 15. 현재 데이터 모델

현재 프로젝트의 핵심 관계는 다음과 같습니다.

```text
┌─────────────────────┐
│       members       │
├─────────────────────┤
│ id                  │
│ email               │
│ name                │
│ password            │
│ token_version       │
│ created_at          │
│ deleted_at          │
└──────────┬──────────┘
           │
           │ 1 : N
           │
┌──────────▼──────────┐
│   refresh_tokens    │
├─────────────────────┤
│ id                  │
│ user_id             │
│ jti                 │
│ expires_at          │
│ revoked_at          │
└─────────────────────┘
```

`members`는 서비스 회원의 상태를 관리하고,
`refresh_tokens`는 해당 회원의 로그인 세션과 Refresh Token 상태를 관리합니다.