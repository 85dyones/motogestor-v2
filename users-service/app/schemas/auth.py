from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, constr


class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class RegisterRequest(BaseModel):
    name: constr(min_length=2, max_length=255)
    email: EmailStr
    password: constr(min_length=6)
    tenant_name: constr(min_length=2, max_length=255) = Field(default="Nova Oficina")


class AuthUser(BaseModel):
    id: int
    name: str
    email: EmailStr
    tenant_id: int
    tenant_name: str | None = None
    plan: str | None = None
    role: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    user: AuthUser
