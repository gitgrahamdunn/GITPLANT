import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)
SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-key")


@dataclass
class CurrentUser:
    email: str
    role: str


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode())


def issue_token(email: str, role: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "email": email,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    payload_part = _b64url_encode(payload_bytes)

    signature = hmac.new(SECRET_KEY.encode(), payload_part.encode(), hashlib.sha256).digest()
    signature_part = _b64url_encode(signature)
    return f"{payload_part}.{signature_part}"


def parse_token(token: str) -> CurrentUser:
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc

    expected_sig = hmac.new(SECRET_KEY.encode(), payload_part.encode(), hashlib.sha256).digest()
    actual_sig = _b64url_decode(signature_part)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    payload = json.loads(_b64url_decode(payload_part).decode())
    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    email = payload.get("email")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return CurrentUser(email=email, role=role)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    return parse_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _checker
