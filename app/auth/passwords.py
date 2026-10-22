from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_ph = PasswordHasher


def hash_password(password: str) -> str:
    return _ph().hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph().verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
