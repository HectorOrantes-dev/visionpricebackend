"""Consulta del perfil completo del usuario autenticado."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.shared.models import Usuario


@dataclass
class Perfil:
    id: int
    nombre: str
    correo: str
    telefono: str | None
    rol: str
    activo: bool
    proveedor_auth: str
    fecha_registro: datetime
    plan_activo: str | None
    vigencia_hasta: datetime | None


async def obtener_perfil(session: AsyncSession, usuario_id: int) -> Perfil | None:
    result = await session.execute(
        select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.id == usuario_id)
    )
    u = result.scalar_one_or_none()
    if u is None:
        return None
    return Perfil(
        id=u.id,
        nombre=u.nombre,
        correo=u.correo,
        telefono=u.telefono,  # EncryptedString lo descifra al leer
        rol=u.rol.nombre,
        activo=u.activo,
        proveedor_auth=u.proveedor_auth,
        fecha_registro=u.fecha_registro,
        plan_activo=u.plan_activo,
        vigencia_hasta=u.vigencia_hasta,
    )
