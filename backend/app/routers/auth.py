from fastapi import APIRouter, HTTPException

from app.schemas import AuthLoginRequest, AuthLoginResponse

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

    return AuthLoginResponse(access_token=f"demo-token-for-{payload.email}", role=user["role"])
