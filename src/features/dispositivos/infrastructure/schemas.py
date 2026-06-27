"""Schemas HTTP de la feature dispositivos."""
from typing import Literal

from pydantic import BaseModel, Field


class RegistrarDispositivoRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512, description="device token FCM")
    plataforma: Literal["android", "ios", "web"]


class EliminarDispositivoRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)


class OkOut(BaseModel):
    ok: bool = True
