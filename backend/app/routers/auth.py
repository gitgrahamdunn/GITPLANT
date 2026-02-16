from fastapi import APIRouter, Depends, HTTPException

from app.schemas import AuthLoginRequest, AuthLoginResponse, AuthMeResponse
from app.security import CurrentUser, get_current_user, issue_token

router = APIRouter(prefix="/auth", tags=["auth"])


DEMO_USERS = {
    "user@edms.local": {"password": "user123", "role": "user"},
}


@router.post("/login", response_model=AuthLoginResponse, summary="Login (MVP demo)")
def login(payload: AuthLoginRequest):
    user = DEMO_USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = issue_token(payload.email, user["role"])
    return AuthLoginResponse(access_token=token, role=user["role"])


@router.get("/me", response_model=AuthMeResponse, summary="Current user")
def me(current_user: CurrentUser = Depends(get_current_user)):
    return AuthMeResponse(email=current_user.email, role=current_user.role)
