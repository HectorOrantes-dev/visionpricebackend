"""Composición de dependencias de la feature equipos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.equipos.application.gestionar_equipo import (
    AgregarMiembro,
    CrearEquipo,
    ListarMiembros,
    ListarMisEquipos,
    QuitarMiembro,
)
from src.features.equipos.infrastructure.repository import (
    SqlAlchemyEquipoRepository,
)


def _repo(session: AsyncSession) -> SqlAlchemyEquipoRepository:
    return SqlAlchemyEquipoRepository(session)


def get_crear_equipo(session: AsyncSession = Depends(get_session)) -> CrearEquipo:
    return CrearEquipo(repo=_repo(session))


def get_listar_equipos(
    session: AsyncSession = Depends(get_session),
) -> ListarMisEquipos:
    return ListarMisEquipos(repo=_repo(session))


def get_agregar_miembro(
    session: AsyncSession = Depends(get_session),
) -> AgregarMiembro:
    return AgregarMiembro(repo=_repo(session))


def get_quitar_miembro(
    session: AsyncSession = Depends(get_session),
) -> QuitarMiembro:
    return QuitarMiembro(repo=_repo(session))


def get_listar_miembros(
    session: AsyncSession = Depends(get_session),
) -> ListarMiembros:
    return ListarMiembros(repo=_repo(session))
