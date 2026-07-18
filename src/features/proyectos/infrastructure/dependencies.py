"""Composición de dependencias de la feature proyectos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.proyectos.application.gestionar_proyecto import (
    ActualizarProyecto,
    CrearProyecto,
    ListarProyectos,
    ObtenerProyecto,
)
from src.features.proyectos.application.membresia import (
    CrearInvitacion,
    ListarInvitaciones,
    ListarMiembros,
    QuitarMiembro,
    RevocarInvitacion,
    UnirseAProyecto,
)
from src.features.proyectos.infrastructure.correo_adapter import CorreoAdapter2FA
from src.features.proyectos.infrastructure.invitacion_repository import (
    SqlAlchemyInvitacionRepository,
)
from src.features.proyectos.infrastructure.membresia_repository import (
    SqlAlchemyMembresiaRepository,
)
from src.features.proyectos.infrastructure.repository import (
    SqlAlchemyProyectoRepository,
)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _repo(session: AsyncSession) -> SqlAlchemyProyectoRepository:
    return SqlAlchemyProyectoRepository(session)


def _mem_repo(session: AsyncSession) -> SqlAlchemyMembresiaRepository:
    return SqlAlchemyMembresiaRepository(session)


def _inv_repo(session: AsyncSession) -> SqlAlchemyInvitacionRepository:
    return SqlAlchemyInvitacionRepository(session)


def _correo() -> CorreoAdapter2FA:
    return CorreoAdapter2FA()


# ---------------------------------------------------------------------------
# Proyectos base
# ---------------------------------------------------------------------------


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
    return ObtenerProyecto(repo=_repo(session), membresia=_mem_repo(session))


def get_actualizar_proyecto(
    session: AsyncSession = Depends(get_session),
) -> ActualizarProyecto:
    return ActualizarProyecto(repo=_repo(session), membresia=_mem_repo(session))


# ---------------------------------------------------------------------------
# Membresía e invitaciones
# ---------------------------------------------------------------------------


def get_crear_invitacion(
    session: AsyncSession = Depends(get_session),
) -> CrearInvitacion:
    return CrearInvitacion(
        membresia_repo=_mem_repo(session),
        inv_repo=_inv_repo(session),
        correo_port=_correo(),
    )


def get_unirse_a_proyecto(
    session: AsyncSession = Depends(get_session),
) -> UnirseAProyecto:
    return UnirseAProyecto(
        membresia_repo=_mem_repo(session),
        inv_repo=_inv_repo(session),
    )


def get_listar_miembros(
    session: AsyncSession = Depends(get_session),
) -> ListarMiembros:
    return ListarMiembros(membresia_repo=_mem_repo(session))


def get_quitar_miembro(
    session: AsyncSession = Depends(get_session),
) -> QuitarMiembro:
    return QuitarMiembro(membresia_repo=_mem_repo(session))


def get_listar_invitaciones(
    session: AsyncSession = Depends(get_session),
) -> ListarInvitaciones:
    return ListarInvitaciones(
        membresia_repo=_mem_repo(session),
        inv_repo=_inv_repo(session),
    )


def get_revocar_invitacion(
    session: AsyncSession = Depends(get_session),
) -> RevocarInvitacion:
    return RevocarInvitacion(
        membresia_repo=_mem_repo(session),
        inv_repo=_inv_repo(session),
    )
