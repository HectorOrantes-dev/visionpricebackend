"""Caso de uso: calcular m² (piso/paredes) desde la transcripción o un texto."""
from dataclasses import dataclass

from src.features.cotizaciones.domain.calculo import calcular_areas, parse_dimensiones
from src.features.cotizaciones.domain.entities import CalculoAreas, Dimensiones
from src.features.cotizaciones.domain.ports import CotizacionRepository
from src.shared.errors import NotFound, ValidationError


@dataclass
class CalcularAreasCommand:
    grabacion_id: int | None = None
    texto: str | None = None
    # Overrides manuales (ej. altura que el regex no detectó): reemplazan la
    # dimensión detectada solo si vienen informados.
    largo_m: float | None = None
    ancho_m: float | None = None
    alto_m: float | None = None


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

        dim = parse_dimensiones(texto)
        dim = Dimensiones(
            largo_m=cmd.largo_m if cmd.largo_m is not None else dim.largo_m,
            ancho_m=cmd.ancho_m if cmd.ancho_m is not None else dim.ancho_m,
            alto_m=cmd.alto_m if cmd.alto_m is not None else dim.alto_m,
        )
        return calcular_areas(dim)
