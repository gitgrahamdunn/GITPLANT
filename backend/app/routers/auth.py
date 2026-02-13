from fastapi import APIRouter, Depends, HTTPException

from app.schemas import AuthLoginRequest, AuthLoginResponse, AuthMeResponse
from app.security import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


DEMO_USERS = {
    "controller@edms.local": {"password": "controller123", "role": "document_controller"},
    "engineer@edms.local": {"password": "engineer123", "role": "engineer"},
    "approver@edms.local": {"password": "approver123", "role": "approver"},
}


@router.post("/login", response_model=AuthLoginResponse, summary="Login (MVP demo)")
def login(payload: AuthLoginRequest):
    user = DEMO_USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"demo-token-for-{payload.email}|{user['role']}"
    return AuthLoginResponse(access_token=token, role=user["role"])


@router.get("/me", response_model=AuthMeResponse, summary="Current user")
def me(current_user: CurrentUser = Depends(get_current_user)):
    return AuthMeResponse(email=current_user.email, role=current_user.role)
