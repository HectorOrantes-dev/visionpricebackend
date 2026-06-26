"""Caso de uso: procesar el resultado que envía el microservicio de ML.

Lo dispara el webhook /api/v1/ml/callback. Persiste la transcripción y la
extracción estructurada en la API principal (las necesita el módulo de
presupuestos) y marca la grabación como sincronizada.
"""
from src.features.grabaciones.domain.entities import ResultadoML
from src.features.grabaciones.domain.ports import GrabacionRepository


class ProcesarResultadoML:
    def __init__(self, repo: GrabacionRepository) -> None:
        self._repo = repo

    async def execute(self, resultado: ResultadoML) -> None:
        await self._repo.guardar_resultado_ml(resultado)
