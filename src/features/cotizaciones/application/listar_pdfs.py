"""Caso de uso: listar todos los PDFs (cotizaciones) que el usuario ha creado,
en todas sus obras, sin importar su rol.
"""
from src.features.cotizaciones.domain.entities import CotizacionPdfItem
from src.features.cotizaciones.domain.ports import CotizacionRepository


class ListarMisPdfs:
    def __init__(self, repo: CotizacionRepository) -> None:
        self._repo = repo

    async def execute(self, usuario_id: int) -> list[CotizacionPdfItem]:
        return await self._repo.listar_pdfs_de_usuario(usuario_id)
