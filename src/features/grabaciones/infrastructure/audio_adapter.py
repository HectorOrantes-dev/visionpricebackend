"""Adaptador del puerto de audio sobre el gateway de Extracciones."""
from src.features.grabaciones.domain.ports import AudioSubmissionPort
from src.microservices.extractions_gateway import ExtractionsGateway


class ExtractionsAudioAdapter(AudioSubmissionPort):
    def __init__(self, gateway: ExtractionsGateway | None = None) -> None:
        self._gateway = gateway or ExtractionsGateway()

    async def submit_audio(
        self,
        *,
        grabacion_id: int,
        user_hash: str,
        proyecto_id: int | None,
        filename: str,
        audio: bytes,
        content_type: str,
    ) -> dict:
        return await self._gateway.submit_audio(
            grabacion_id=grabacion_id,
            user_hash=user_hash,
            proyecto_id=proyecto_id,
            filename=filename,
            audio=audio,
            content_type=content_type,
        )
