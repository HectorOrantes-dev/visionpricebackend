"""Schemas HTTP de la feature roles."""
from pydantic import BaseModel


class RolOut(BaseModel):
    id: int
    nombre: str
