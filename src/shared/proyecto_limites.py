"""Tope de cotizaciones/PDFs de un PROYECTO (equipo).

Distinto de `src/shared/plan_limites.py` (cuota gratis POR USUARIO, se
levanta con un plan pagado). Este es un tope duro del proyecto compartido:
10 cotizaciones/PDFs entre TODOS sus miembros, fijo, no se relaciona con el
plan de nadie — así lo pidió el usuario explícitamente.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.errors import ProyectoLimiteAlcanzado
from src.shared.models import Presupuesto

LIMITE_PDFS_POR_PROYECTO = 10


async def verificar_limite_proyecto(session: AsyncSession, proyecto_id: int) -> None:
    total = await session.scalar(
        select(func.count())
        .select_from(Presupuesto)
        .where(Presupuesto.proyecto_id == proyecto_id)
    )
    usadas = total or 0
    if usadas >= LIMITE_PDFS_POR_PROYECTO:
        raise ProyectoLimiteAlcanzado(
            f"Este proyecto ya alcanzó el límite de "
            f"{LIMITE_PDFS_POR_PROYECTO} cotizaciones/PDFs entre todos sus "
            "miembros.",
            details={"limite": LIMITE_PDFS_POR_PROYECTO, "usadas": usadas},
        )
