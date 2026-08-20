from pwdlib import PasswordHash


# 비밀번호 해싱 객체
password_hash = PasswordHash.recommended()


# 비밀번호를 해시한다.
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# 입력한 비밀번호가 해시와 일치하는지 확인한다.
def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        password,
        hashed_password
    )