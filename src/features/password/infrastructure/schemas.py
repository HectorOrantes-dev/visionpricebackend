"""Schemas HTTP del restablecimiento de contraseña."""
from pydantic import BaseModel, EmailStr, Field


class ForgotRequest(BaseModel):
    correo: EmailStr


class ResetRequest(BaseModel):
    correo: EmailStr
    code: str = Field(min_length=4, max_length=10)
    nueva_contrasena: str = Field(min_length=8, max_length=128)


class MessageOut(BaseModel):
    message: str
