"""Adaptador SQLAlchemy del repositorio de grabaciones."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.grabaciones.domain.entities import (
    Grabacion,
    NuevaGrabacion,
    ResultadoML,
)
from src.features.grabaciones.domain.ports import GrabacionRepository
from src.shared.errors import NotFound
from src.shared.models import ExtraccionLLM, GrabacionAudio, Transcripcion


class SqlAlchemyGrabacionRepository(GrabacionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, nueva: NuevaGrabacion) -> Grabacion:
        fila = GrabacionAudio(
            usuario_id=nueva.usuario_id,
            proyecto_id=nueva.proyecto_id,
            duracion_segundos=nueva.duracion_segundos,
            hash_archivo=nueva.hash_archivo,
            fecha_grabacion=nueva.fecha_grabacion,
            estado_sincronizacion="pendiente",
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return Grabacion(
            id=fila.id,
            usuario_id=fila.usuario_id,
            proyecto_id=fila.proyecto_id,
            object_storage_key=fila.object_storage_key,
            estado_sincronizacion=fila.estado_sincronizacion,
        )

    async def marcar_enviada(
        self, grabacion_id: int, object_storage_key: str | None
    ) -> None:
        fila = await self._session.get(GrabacionAudio, grabacion_id)
        if fila is None:
            raise NotFound("Grabación no encontrada.")
        fila.object_storage_key = object_storage_key
        fila.estado_sincronizacion = "procesando"
        await self._session.commit()

    async def guardar_resultado_ml(self, resultado: ResultadoML) -> None:
        fila = await self._session.get(GrabacionAudio, resultado.grabacion_id)
        if fila is None:
            raise NotFound("Grabación no encontrada.")

        if resultado.object_storage_key:
            fila.object_storage_key = resultado.object_storage_key

        # Idempotencia: si ya hay transcripción para esta grabación, reusa.
        existing = await self._session.execute(
            select(Transcripcion).where(
                Transcripcion.grabacion_id == resultado.grabacion_id
            )
        )
        transcripcion = existing.scalar_one_or_none()
        if transcripcion is None:
            transcripcion = Transcripcion(
                grabacion_id=resultado.grabacion_id,
                texto=resultado.texto,
                modelo_voice_to_text=resultado.modelo_voice_to_text,
                confianza=resultado.confianza,
            )
            self._session.add(transcripcion)
            await self._session.flush()
        else:
            transcripcion.texto = resultado.texto
            transcripcion.modelo_voice_to_text = resultado.modelo_voice_to_text
            transcripcion.confianza = resultado.confianza

        existing_ext = await self._session.execute(
            select(ExtraccionLLM).where(
                ExtraccionLLM.transcripcion_id == transcripcion.id
            )
        )
        extraccion = existing_ext.scalar_one_or_none()
        if extraccion is None:
            self._session.add(
                ExtraccionLLM(
                    transcripcion_id=transcripcion.id,
                    parametros_json=resultado.parametros_json,
                    version_modelo=resultado.version_modelo,
                )
            )
        else:
            extraccion.parametros_json = resultado.parametros_json
            extraccion.version_modelo = resultado.version_modelo

        fila.estado_sincronizacion = "sincronizado"
        fila.fecha_sincronizacion = datetime.now(timezone.utc)
        await self._session.commit()
