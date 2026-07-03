"""Schemas HTTP del restablecimiento de contraseña."""
from pydantic import BaseModel, EmailStr, Field, model_validator


class ForgotRequest(BaseModel):
    correo: EmailStr


class VerifyCodeRequest(BaseModel):
    correo: EmailStr
    code: str = Field(min_length=4, max_length=10)


class VerifyCodeResponse(BaseModel):
    valid: bool = True
    reset_token: str


class ResetRequest(BaseModel):
    correo: EmailStr
    nueva_contrasena: str = Field(min_length=8, max_length=128)
    # Una de las dos (reset_token es el flujo recomendado):
    reset_token: str | None = None
    code: str | None = Field(default=None, min_length=4, max_length=10)

    @model_validator(mode="after")
    def _una_credencial(self) -> "ResetRequest":
        if not self.reset_token and not self.code:
            raise ValueError("Proporciona reset_token o code.")
        return self


class MessageOut(BaseModel):
    message: str
