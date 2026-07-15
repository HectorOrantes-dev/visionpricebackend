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
    # dimensión detectada solo si vienen informados. Sirven para el caso
    # "cuarto completo" (largo × ancho de piso + altura → perímetro de paredes).
    largo_m: float | None = None
    ancho_m: float | None = None
    alto_m: float | None = None
    # Overrides de área FINAL: para cuando el usuario mide una sola superficie
    # directamente (ej. "una pared de 2×2 m") en vez de un cuarto completo.
    # Saltan la fórmula de perímetro por completo y reemplazan el resultado.
    piso_m2: float | None = None
    paredes_m2: float | None = None


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
        calc = calcular_areas(dim)

        if cmd.piso_m2 is None and cmd.paredes_m2 is None:
            return calc

        # Área directa de una superficie puntual: no aplica la fórmula de
        # perímetro, así que las advertencias de "falta largo/ancho/altura"
        # dejan de ser relevantes para la dimensión que se sobreescribió.
        advertencias = list(calc.advertencias)
        if cmd.piso_m2 is not None:
            advertencias = [a for a in advertencias if "el piso" not in a]
        if cmd.paredes_m2 is not None:
            advertencias = [a for a in advertencias if "las paredes" not in a]

        return CalculoAreas(
            largo_m=dim.largo_m,
            ancho_m=dim.ancho_m,
            alto_m=dim.alto_m,
            piso_m2=cmd.piso_m2 if cmd.piso_m2 is not None else calc.piso_m2,
            paredes_m2=cmd.paredes_m2 if cmd.paredes_m2 is not None else calc.paredes_m2,
            advertencias=advertencias,
        )
