"""Caso de uso: registrar una grabación y enviar el audio al microservicio ML.

La API principal es dueña de la RELACIÓN de negocio (usuario, proyecto) y
guarda sólo metadatos + la referencia al audio. El binario lo guarda el
microservicio de ML en su object storage.
"""
import hashlib
from dataclasses import dataclass

from src.features.grabaciones.domain.entities import Grabacion, NuevaGrabacion
from src.features.grabaciones.domain.ports import (
    AudioSubmissionPort,
    GrabacionRepository,
)
from src.shared.timeutils import utcnow


@dataclass
class RegistrarGrabacionCommand:
    usuario_id: int
    user_hash: str
    proyecto_id: int | None
    filename: str
    content_type: str
    audio: bytes
    duracion_segundos: int | None = None


class RegistrarGrabacion:
    def __init__(
        self, repo: GrabacionRepository, audio_port: AudioSubmissionPort
    ) -> None:
        self._repo = repo
        self._audio = audio_port

    async def execute(self, cmd: RegistrarGrabacionCommand) -> Grabacion:
        grabacion = await self._repo.crear(
            NuevaGrabacion(
                usuario_id=cmd.usuario_id,
                proyecto_id=cmd.proyecto_id,
                duracion_segundos=cmd.duracion_segundos,
                hash_archivo=hashlib.sha256(cmd.audio).hexdigest(),
                fecha_grabacion=utcnow(),
            )
        )

        # Atómico: si no se pudo enviar al microservicio de ML, se borra la fila
        # para no dejar grabaciones huérfanas (la app reintenta desde su cola).
        try:
            ack = await self._audio.submit_audio(
                grabacion_id=grabacion.id,
                user_hash=cmd.user_hash,
                proyecto_id=cmd.proyecto_id,
                filename=cmd.filename,
                audio=cmd.audio,
                content_type=cmd.content_type,
            )
        except Exception:
            await self._repo.eliminar(grabacion.id)
            raise

        object_key = ack.get("object_storage_key") if isinstance(ack, dict) else None
        await self._repo.marcar_enviada(grabacion.id, object_key)
        grabacion.object_storage_key = object_key
        grabacion.estado_sincronizacion = "procesando"
        return grabacion
