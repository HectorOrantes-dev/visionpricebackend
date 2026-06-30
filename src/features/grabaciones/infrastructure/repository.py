"""Adaptador SQLAlchemy del repositorio de grabaciones."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.grabaciones.domain.entities import (
    Grabacion,
    GrabacionDetalle,
    GrabacionResumen,
    NuevaGrabacion,
    ResultadoML,
)
from src.features.grabaciones.domain.ports import GrabacionRepository
from src.shared.errors import NotFound
from src.shared.models import ExtraccionLLM, GrabacionAudio, Transcripcion
from src.shared.timeutils import utcnow


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

    async def listar_de(self, usuario_id: int) -> list[GrabacionResumen]:
        result = await self._session.execute(
            select(GrabacionAudio, Transcripcion.id)
            .outerjoin(
                Transcripcion,
                Transcripcion.grabacion_id == GrabacionAudio.id,
            )
            .where(GrabacionAudio.usuario_id == usuario_id)
            .order_by(GrabacionAudio.id.desc())
        )
        return [
            GrabacionResumen(
                id=g.id,
                proyecto_id=g.proyecto_id,
                estado_sincronizacion=g.estado_sincronizacion,
                duracion_segundos=g.duracion_segundos,
                fecha_grabacion=g.fecha_grabacion,
                fecha_sincronizacion=g.fecha_sincronizacion,
                tiene_transcripcion=transcripcion_id is not None,
            )
            for g, transcripcion_id in result.all()
        ]

    async def obtener_detalle(
        self, grabacion_id: int, usuario_id: int
    ) -> GrabacionDetalle | None:
        g = await self._session.get(GrabacionAudio, grabacion_id)
        if g is None or g.usuario_id != usuario_id:
            return None

        result = await self._session.execute(
            select(Transcripcion).where(
                Transcripcion.grabacion_id == grabacion_id
            )
        )
        transcripcion = result.scalar_one_or_none()

        extraccion = None
        if transcripcion is not None:
            res_ext = await self._session.execute(
                select(ExtraccionLLM).where(
                    ExtraccionLLM.transcripcion_id == transcripcion.id
                )
            )
            extraccion = res_ext.scalar_one_or_none()

        return GrabacionDetalle(
            id=g.id,
            proyecto_id=g.proyecto_id,
            estado_sincronizacion=g.estado_sincronizacion,
            object_storage_key=g.object_storage_key,
            duracion_segundos=g.duracion_segundos,
            fecha_grabacion=g.fecha_grabacion,
            fecha_sincronizacion=g.fecha_sincronizacion,
            transcripcion=transcripcion.texto if transcripcion else None,
            modelo_voice_to_text=(
                transcripcion.modelo_voice_to_text if transcripcion else None
            ),
            confianza=(
                float(transcripcion.confianza)
                if transcripcion and transcripcion.confianza is not None
                else None
            ),
            extraccion_json=extraccion.parametros_json if extraccion else None,
            version_modelo=extraccion.version_modelo if extraccion else None,
        )

    async def eliminar(self, grabacion_id: int) -> None:
        fila = await self._session.get(GrabacionAudio, grabacion_id)
        if fila is not None:
            await self._session.delete(fila)
            await self._session.commit()

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
        fila.fecha_sincronizacion = utcnow()
        await self._session.commit()
