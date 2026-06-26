"""Schemas Pydantic compartidos entre features."""
from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str = "ok"
    environment: str


class MessageOut(BaseModel):
    message: str
