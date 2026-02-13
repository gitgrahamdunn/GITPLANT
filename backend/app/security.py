from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    email: str
    role: str


def parse_demo_token(token: str) -> CurrentUser:
    # token format: demo-token-for-{email}|{role}
    prefix = "demo-token-for-"
    if not token.startswith(prefix) or "|" not in token:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = token[len(prefix) :]
    email, role = payload.rsplit("|", maxsplit=1)
    if not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return CurrentUser(email=email, role=role)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    return parse_demo_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _checker
