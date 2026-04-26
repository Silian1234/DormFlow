from __future__ import annotations

import hashlib
import secrets


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, raw_iterations, salt, expected = password_hash.split("$", 3)
        iterations = int(raw_iterations)
    except ValueError:
        return False
    if algorithm != PASSWORD_ALGORITHM:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return secrets.compare_digest(actual, expected)


def make_token() -> str:
    return secrets.token_urlsafe(36)

