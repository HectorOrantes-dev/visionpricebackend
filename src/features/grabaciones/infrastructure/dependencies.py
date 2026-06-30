"""Composición de dependencias de la feature grabaciones."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.grabaciones.application.consultar_grabaciones import (
    ListarGrabaciones,
    ObtenerGrabacion,
)
from src.features.grabaciones.application.procesar_resultado_ml import (
    ProcesarResultadoML,
)
from src.features.grabaciones.application.registrar_grabacion import (
    RegistrarGrabacion,
)
from src.features.grabaciones.infrastructure.audio_adapter import (
    ExtractionsAudioAdapter,
)
from src.features.grabaciones.infrastructure.repository import (
    SqlAlchemyGrabacionRepository,
)


def get_registrar_grabacion(
    session: AsyncSession = Depends(get_session),
) -> RegistrarGrabacion:
    return RegistrarGrabacion(
        repo=SqlAlchemyGrabacionRepository(session),
        audio_port=ExtractionsAudioAdapter(),
    )


def get_procesar_resultado_ml(
    session: AsyncSession = Depends(get_session),
) -> ProcesarResultadoML:
    return ProcesarResultadoML(repo=SqlAlchemyGrabacionRepository(session))


def get_listar_grabaciones(
    session: AsyncSession = Depends(get_session),
) -> ListarGrabaciones:
    return ListarGrabaciones(repo=SqlAlchemyGrabacionRepository(session))


def get_obtener_grabacion(
    session: AsyncSession = Depends(get_session),
) -> ObtenerGrabacion:
    return ObtenerGrabacion(repo=SqlAlchemyGrabacionRepository(session))
