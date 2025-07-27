import secrets
import time
from typing import Dict, Tuple

_otp_store: Dict[str, Tuple[str, float]] = {}

OTP_TTL = 300  # seconds


def generate_otp(email: str) -> str:
    otp = secrets.token_hex(3)
    expires = time.time() + OTP_TTL
    _otp_store[email] = (otp, expires)
    return otp


def verify_and_consume_otp(email: str, otp: str) -> bool:
    saved = _otp_store.get(email)
    if not saved:
        return False
    code, expires = saved
    if time.time() > expires or code != otp:
        return False
    del _otp_store[email]
    return True
