"""Caso de uso: generar el PDF de una cotización (al vuelo, sin guardar)."""
from src.features.cotizaciones.domain.ports import CotizacionRepository, PdfRenderer
from src.shared.errors import NotFound


class GenerarPdf:
    def __init__(self, repo: CotizacionRepository, renderer: PdfRenderer) -> None:
        self._repo = repo
        self._renderer = renderer

    async def execute(self, cotizacion_id: int, usuario_id: int) -> bytes:
        cotizacion = await self._repo.obtener(cotizacion_id, usuario_id)
        if cotizacion is None:
            raise NotFound("Cotización no encontrada.")
        return self._renderer.render(cotizacion)
