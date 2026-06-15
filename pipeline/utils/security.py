"""
utils/security.py — Cryptographic hashing.
"""
import hashlib
import secrets


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"


def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    try:
        salt, stored_key_hex = stored_password_hash.split('$')
        provided_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return provided_key.hex() == stored_key_hex
    except Exception:
        return False
