"""Composición de dependencias de la feature cotizaciones."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.cotizaciones.application.calcular_areas import CalcularAreas
from src.features.cotizaciones.application.crear_cotizacion import CrearCotizacion
from src.features.cotizaciones.application.generar_pdf import GenerarPdf
from src.features.cotizaciones.application.listar_productos import (
    ListarProductosCercanos,
)
from src.features.cotizaciones.infrastructure.pdf import ReportLabPdfRenderer
from src.features.cotizaciones.infrastructure.proveedores_adapter import (
    ProvidersAdapter,
)
from src.features.cotizaciones.infrastructure.repository import (
    SqlAlchemyCotizacionRepository,
)


def get_calcular_areas(
    session: AsyncSession = Depends(get_session),
) -> CalcularAreas:
    return CalcularAreas(repo=SqlAlchemyCotizacionRepository(session))


def get_listar_productos() -> ListarProductosCercanos:
    return ListarProductosCercanos(proveedores=ProvidersAdapter())


def get_crear_cotizacion(
    session: AsyncSession = Depends(get_session),
) -> CrearCotizacion:
    return CrearCotizacion(
        repo=SqlAlchemyCotizacionRepository(session),
        proveedores=ProvidersAdapter(),
        merma=settings.cotizacion_merma,
    )


def get_generar_pdf(
    session: AsyncSession = Depends(get_session),
) -> GenerarPdf:
    return GenerarPdf(
        repo=SqlAlchemyCotizacionRepository(session),
        renderer=ReportLabPdfRenderer(),
    )
