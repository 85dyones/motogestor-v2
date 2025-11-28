from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    tenant_id: int
    role: str | None = None
    plan: str | None = None


class SeedDemoResponse(BaseModel):
    message: str
    tenant: dict
    user: dict
    credentials: dict
