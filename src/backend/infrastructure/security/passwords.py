from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_password_hash = PasswordHash.recommended()
_dummy_hash = _password_hash.hash("not-a-real-user-password")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_and_update_password(password: str, password_hash: str | None) -> tuple[bool, str | None]:
    candidate_hash = password_hash or _dummy_hash
    try:
        valid, updated_hash = _password_hash.verify_and_update(password, candidate_hash)
    except UnknownHashError:
        return False, None
    if password_hash is None:
        return False, None
    return valid, updated_hash
