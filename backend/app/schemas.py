from pydantic import BaseModel, EmailStr


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
