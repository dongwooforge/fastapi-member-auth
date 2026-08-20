import os

from dotenv import load_dotenv


# 프로젝트 루트의 .env 파일을 읽는다.
load_dotenv()


# ========================================
# Database
# ========================================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError(
        "DATABASE_URL 환경변수가 설정되지 않았습니다."
    )


# ========================================
# JWT
# ========================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if JWT_SECRET_KEY is None:
    raise RuntimeError(
        "JWT_SECRET_KEY 환경변수가 설정되지 않았습니다."
    )


JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv(
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
        "7"
    )
)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)

