# FastAPI Member Auth

FastAPI 기반의 회원 관리 및 JWT 인증 API 프로젝트입니다.

단순 CRUD 구현을 넘어 Access/Refresh Token 분리, Refresh Token Rotation,
토큰 재사용 탐지, 비밀번호 변경 시 기존 세션 무효화, Soft Delete 등의
인증 및 보안 흐름을 구현합니다.

---

## Tech Stack

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic

### Database
- MySQL 8.4
- Docker

### Authentication
- JWT Access Token
- JWT Refresh Token
- Password Hashing

### Test
- pytest
- FastAPI TestClient
- Test Database 분리

---

## 주요 기능

### 회원 관리
- 회원가입
- 이메일 형식 검증
- 비밀번호 정책 검증
- 이메일 중복 방지
- 내 회원정보 조회
- 내 회원정보 수정
- 비밀번호 변경
- 회원 탈퇴

### 인증
- 이메일 / 비밀번호 로그인
- JWT Access Token 발급
- JWT Refresh Token 발급
- Access Token 기반 API 인증
- Refresh Token 기반 Access Token 재발급

### 보안
- 비밀번호 Hash 저장
- Refresh Token DB 관리
- Refresh Token Rotation
- 사용된 Refresh Token 재사용 탐지
- 재사용 탐지 시 해당 사용자의 모든 Refresh Token 폐기
- 비밀번호 변경 시 기존 Access Token 무효화
- 비밀번호 변경 시 모든 Refresh Token 폐기
- 회원 탈퇴 시 기존 로그인 세션 무효화

### 회원 탈퇴
회원 데이터는 즉시 물리 삭제하지 않고 Soft Delete 방식으로 처리합니다.

- `deleted_at` 기록
- `token_version` 증가
- 기존 Access Token 무효화
- 모든 Refresh Token 폐기
- 탈퇴 회원 로그인 차단
- 탈퇴 회원 정보 조회 및 수정 차단

---

## Authentication Flow

### 로그인

```text
Email + Password
       ↓
사용자 인증
       ↓
Access Token + Refresh Token 발급
       ↓
Refresh Token 정보 DB 저장
```

### Access Token 재발급

```text
Refresh Token A
       ↓
JWT 검증
       ↓
DB 상태 검증
       ↓
Refresh Token A 폐기
       ↓
새 Access Token
+
Refresh Token B 발급
```

Refresh Token은 한 번 사용되면 폐기되는 Rotation 방식을 사용합니다.

이미 사용된 Refresh Token이 다시 사용될 경우 토큰 탈취 가능성이 있다고 판단하여
해당 사용자의 모든 Refresh Token을 폐기합니다.

---

## Project Structure

```text
fastapi/
├── app/
│   ├── auth/
│   │   ├── db.py
│   │   ├── dependencies.py
│   │   ├── jwt.py
│   │   ├── model.py
│   │   └── service.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   └── connection.py
│   │
│   ├── members/
│   │   ├── db.py
│   │   ├── model.py
│   │   ├── router.py
│   │   ├── schema.py
│   │   ├── security.py
│   │   └── service.py
│   │
│   ├── config.py
│   └── main.py
│
├── docs/
│   └── api.md
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_members.py
│
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| POST | `/members` | 회원가입 | 없음 |
| POST | `/login` | 로그인 | 없음 |
| POST | `/refresh` | Access/Refresh Token 재발급 | Refresh Token |
| POST | `/logout` | 로그아웃 | Refresh Token |
| GET | `/members/me` | 내 회원정보 조회 | Access Token |
| PATCH | `/members/me` | 내 회원정보 수정 | Access Token |
| PATCH | `/members/me/password` | 비밀번호 변경 | Access Token |
| DELETE | `/members/me` | 회원 탈퇴 | Access Token |

자세한 요청/응답 및 오류 명세는 [`docs/api.md`](docs/api.md)를 참고하세요.

---

## Environment Variables

민감한 설정값은 `.env` 파일을 통해 관리하며 Git에 포함하지 않습니다.

필요한 환경변수:

```text
DATABASE_URL
TEST_DATABASE_URL

JWT_SECRET_KEY
JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS
```

---

## Database

MySQL은 Docker를 사용하여 실행합니다.

```bash
docker compose up -d
```

컨테이너 상태 확인:

```bash
docker ps
```

---

## Run

가상환경을 활성화한 뒤 FastAPI 서버를 실행합니다.

```bash
uvicorn app.main:app --reload
```

서버 실행 후 Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Test

테스트는 실제 서비스 DB와 분리된 Test Database를 사용합니다.

전체 테스트 실행:

```bash
pytest -v
```

현재 테스트 범위:

- 회원가입 성공
- 이메일 중복 가입 차단
- 이메일 형식 검증
- 비밀번호 정책 검증
- 로그인 성공 / 실패
- Access Token 인증
- 인증되지 않은 요청 차단
- Refresh Token Rotation
- Refresh Token 재사용 탐지
- 로그아웃 후 Refresh Token 사용 차단
- 비밀번호 변경 후 기존 Access Token 무효화
- Soft Delete
- 잘못된 비밀번호를 이용한 회원 탈퇴 차단
- 탈퇴 회원의 회원정보 수정 차단

---

## Security Design

### Access Token

짧은 유효기간을 가지며 API 인증에 사용합니다.

JWT의 `token_version`과 DB의 회원 `token_version`을 비교하여
비밀번호 변경이나 회원 탈퇴 이후 기존 Access Token을 즉시 무효화할 수 있습니다.

### Refresh Token

Refresh Token의 `jti`를 DB에서 관리합니다.

토큰 재발급 시 기존 Refresh Token을 폐기하고 새로운 Refresh Token을 발급합니다.

폐기된 Refresh Token이 다시 사용될 경우 재사용 공격 가능성이 있다고 판단하여
해당 사용자의 모든 Refresh Token을 폐기합니다.

### Password

비밀번호 원문은 DB에 저장하지 않으며 Hash 값만 저장합니다.

### Soft Delete

회원 탈퇴 시 회원 row를 즉시 삭제하지 않고 `deleted_at`을 기록합니다.

탈퇴와 동시에 기존 인증 토큰을 무효화하고 이후 로그인 및 회원 기능 접근을 차단합니다.

---

## Development Workflow

기능 추가 및 변경은 다음 흐름을 기준으로 진행합니다.

```text
Implementation
     ↓
Test
     ↓
Regression Test
     ↓
Documentation
     ↓
Git Commit
```

코드, 테스트, 문서가 서로 일치하도록 유지하는 것을 목표로 합니다.

## Documentation

- [`API Documentation`](docs/api.md) - 엔드포인트, 요청/응답, 인증 요구사항
- [`Authentication`](docs/authentication.md) - JWT, Refresh Token Rotation, 토큰 무효화 구조
- [`Database`](docs/database.md) - 데이터 모델, Soft Delete, Refresh Token 저장 구조