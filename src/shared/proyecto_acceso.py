"""Helper compartido: verifica si un usuario puede acceder a un proyecto.

Útil para features que no dependen del repositorio de proyectos directamente
(cotizaciones, grabaciones) sin crear un acoplamiento entre features.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.models import Proyecto, ProyectoColaborador


async def puede_acceder(
    session: AsyncSession, proyecto_id: int, usuario_id: int
) -> bool:
    """True si el usuario es dueño del proyecto O colaborador registrado."""
    # ¿Es dueño?
    row = await session.execute(
        select(Proyecto.id).where(
            Proyecto.id == proyecto_id,
            Proyecto.usuario_id == usuario_id,
        )
    )
    if row.scalar_one_or_none() is not None:
        return True

    # ¿Es colaborador?
    row = await session.execute(
        select(ProyectoColaborador.proyecto_id).where(
            ProyectoColaborador.proyecto_id == proyecto_id,
            ProyectoColaborador.usuario_id == usuario_id,
        )
    )
    return row.scalar_one_or_none() is not None
