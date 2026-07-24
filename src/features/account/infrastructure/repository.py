"""Consulta del perfil completo del usuario autenticado."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.shared.models import Usuario

# Nombre/precio amigables por plan_key — mismos plan_key que el catálogo del
# microservicio de Pagos (src/shared/plan_catalog.py ahí). Se duplica acá
# nada más lo cosmético (nombre y precio); la fuente de verdad de la
# facturación sigue siendo Pagos, esto solo es para no mostrar el slug crudo
# ("vision-price-pro") en el perfil.
_PLANES = {
    "vision-price-pro": {"nombre": "Pro", "precio_mxn": 349},
    "vision-price-plan": {"nombre": "Plan", "precio_mxn": 899},
}


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
    plan_nombre: str | None
    plan_precio_mxn: int | None
    vigencia_hasta: datetime | None


async def actualizar_perfil(
    session: AsyncSession,
    usuario_id: int,
    *,
    nombre: str | None = None,
    telefono: str | None = None,
) -> Perfil | None:
    """Actualiza solo los campos provistos (no-`None`) del perfil.

    Pensado para el registro simplificado (correo+contraseña+rol): el
    `nombre`/`teléfono` reales se completan después, aquí — no en el alta.
    """
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    u = result.scalar_one_or_none()
    if u is None:
        return None
    if nombre is not None:
        u.nombre = nombre
    if telefono is not None:
        u.telefono = telefono  # EncryptedString lo cifra al guardar
    await session.commit()
    return await obtener_perfil(session, usuario_id)


async def obtener_perfil(session: AsyncSession, usuario_id: int) -> Perfil | None:
    result = await session.execute(
        select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.id == usuario_id)
    )
    u = result.scalar_one_or_none()
    if u is None:
        return None
    plan_info = _PLANES.get(u.plan_activo) if u.plan_activo else None
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
        plan_nombre=plan_info["nombre"] if plan_info else None,
        plan_precio_mxn=plan_info["precio_mxn"] if plan_info else None,
        vigencia_hasta=u.vigencia_hasta,
    )
