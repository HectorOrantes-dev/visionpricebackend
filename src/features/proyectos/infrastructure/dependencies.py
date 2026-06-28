"""Composición de dependencias de la feature proyectos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.proyectos.application.gestionar_proyecto import (
    ActualizarProyecto,
    CrearProyecto,
    ListarProyectos,
    ObtenerProyecto,
)
from src.features.proyectos.infrastructure.repository import (
    SqlAlchemyProyectoRepository,
)


def _repo(session: AsyncSession) -> SqlAlchemyProyectoRepository:
    return SqlAlchemyProyectoRepository(session)


def get_crear_proyecto(
    session: AsyncSession = Depends(get_session),
) -> CrearProyecto:
    return CrearProyecto(repo=_repo(session))


def get_listar_proyectos(
    session: AsyncSession = Depends(get_session),
) -> ListarProyectos:
    return ListarProyectos(repo=_repo(session))


def get_obtener_proyecto(
    session: AsyncSession = Depends(get_session),
) -> ObtenerProyecto:
    return ObtenerProyecto(repo=_repo(session))


def get_actualizar_proyecto(
    session: AsyncSession = Depends(get_session),
) -> ActualizarProyecto:
    return ActualizarProyecto(repo=_repo(session))
