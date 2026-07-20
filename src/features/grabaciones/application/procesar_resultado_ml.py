"""Caso de uso: procesar el resultado que envía el microservicio de ML.

Lo dispara el webhook /api/v1/ml/callback. Persiste la transcripción y la
extracción estructurada en la API principal (las necesita el módulo de
presupuestos) y marca la grabación como sincronizada. Al terminar, notifica al
usuario por push (GRABACION_PROCESADA en éxito, GRABACION_ERROR si el micro
reportó un fallo) para que la app ya no dependa del polling.
"""
import logging

from src.features.grabaciones.domain.entities import ResultadoML
from src.features.grabaciones.domain.ports import GrabacionRepository
from src.features.notificaciones.application.emitir_evento import (
    EmitirEvento,
    EventoCommand,
)
from src.features.notificaciones.domain.entities import TipoNotificacion

_log = logging.getLogger("grabaciones.notificar")


class ProcesarResultadoML:
    def __init__(
        self, repo: GrabacionRepository, emitir: EmitirEvento | None = None
    ) -> None:
        self._repo = repo
        self._emitir = emitir

    async def execute(self, resultado: ResultadoML) -> None:
        usuario_id = await self._repo.guardar_resultado_ml(resultado)

        if self._emitir is None:
            return

        tipo = (
            TipoNotificacion.GRABACION_ERROR
            if resultado.error
            else TipoNotificacion.GRABACION_PROCESADA
        )
        # Best-effort: si falla la notificación, el callback igual responde 200
        # (la transcripción ya se guardó; el push no debe tumbar el webhook).
        try:
            await self._emitir.execute(
                EventoCommand(
                    usuario_id=usuario_id,
                    tipo=tipo,
                    referencia_tipo="grabacion",
                    referencia_id=resultado.grabacion_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning(
                "No se pudo emitir %s para grabacion %s: %s",
                tipo,
                resultado.grabacion_id,
                exc,
            )
