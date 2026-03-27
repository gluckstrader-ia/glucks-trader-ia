from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=120)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=120)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    is_active: bool
    is_blocked: bool
    is_admin: bool

    plan: str
    plan_status: str
    access_expires_at: Optional[datetime]
    has_access: bool

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserStatusUpdateResponse(BaseModel):
    message: str
    user: UserResponse


class ActivateUserRequest(BaseModel):
    plan: Optional[str] = "mensal"


class BlockUserRequest(BaseModel):
    reason: Optional[str] = None

class RenewUserRequest(BaseModel):
    plan: Optional[str] = "mensal"