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

class GenerarPdfProyecto:
    def __init__(self, repo: CotizacionRepository, renderer: PdfRenderer) -> None:
        self._repo = repo
        self._renderer = renderer

    async def execute(self, proyecto_id: int, usuario_id: int) -> bytes:
        info_proyecto = await self._repo.obtener_info_proyecto(proyecto_id, usuario_id)
        if not info_proyecto:
            raise NotFound("Proyecto no encontrado.")

        cotizaciones = await self._repo.listar_cotizaciones_de_proyecto(proyecto_id, usuario_id)
        if not cotizaciones:
            raise NotFound("No hay cotizaciones para este proyecto.")
        return self._renderer.render_proyecto(cotizaciones, proyecto_id, info_proyecto)
