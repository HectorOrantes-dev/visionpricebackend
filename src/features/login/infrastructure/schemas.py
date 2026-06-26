"""Schemas HTTP de la feature login."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=128)


class LoginChallengeOut(BaseModel):
    correo: EmailStr
    two_factor_required: bool = True
    two_factor_sent: bool
    message: str


class VerifyRequest(BaseModel):
    correo: EmailStr
    code: str = Field(min_length=4, max_length=10)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    correo: EmailStr
    rol: str
