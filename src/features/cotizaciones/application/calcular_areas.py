"""Caso de uso: calcular m² (piso/paredes) desde la transcripción o un texto."""
from dataclasses import dataclass

from src.features.cotizaciones.domain.calculo import calcular_desde_texto
from src.features.cotizaciones.domain.entities import CalculoAreas
from src.features.cotizaciones.domain.ports import CotizacionRepository
from src.shared.errors import NotFound, ValidationError


@dataclass
class CalcularAreasCommand:
    grabacion_id: int | None = None
    texto: str | None = None


class CalcularAreas:
    def __init__(self, repo: CotizacionRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CalcularAreasCommand) -> CalculoAreas:
        texto = cmd.texto
        if texto is None:
            if cmd.grabacion_id is None:
                raise ValidationError("Indica grabacion_id o texto.")
            texto = await self._repo.texto_transcripcion(cmd.grabacion_id)
            if texto is None:
                raise NotFound(
                    "No hay transcripción para esa grabación todavía."
                )
        return calcular_desde_texto(texto)
