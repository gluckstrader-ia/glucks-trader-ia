from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=120)

    phone: str = Field(..., min_length=10, max_length=20)
    address_number: Optional[str] = Field(default=None, max_length=20)

    # Código digitado manualmente pelo cliente no cadastro
    referred_by_code: Optional[str] = None

    # Aceita também este nome para compatibilidade com o frontend
    partner_code: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=120)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    phone: Optional[str] = None
    address_number: Optional[str] = None

    is_active: bool
    is_blocked: bool
    is_admin: bool

    plan: str
    plan_status: str
    access_expires_at: Optional[datetime]
    has_access: bool

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # Dados de parceiro/afiliado
    is_partner: Optional[bool] = False
    partner_code: Optional[str] = None
    partner_status: Optional[str] = None
    partner_pix_key: Optional[str] = None
    partner_pix_type: Optional[str] = None

    # Código do afiliado que indicou o cliente
    referred_by_user_id: Optional[int] = None
    referred_by_code: Optional[str] = None
    affiliate_code: Optional[str] = None

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