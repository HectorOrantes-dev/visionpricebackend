"""Composición de dependencias de la feature cotizaciones."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.cotizaciones.application.calcular_areas import CalcularAreas
from src.features.cotizaciones.application.crear_cotizacion import CrearCotizacion
from src.features.cotizaciones.application.crear_kit import CrearCotizacionKit
from src.features.cotizaciones.application.generar_borrador import (
    GenerarBorradorCotizacion,
)
from src.features.cotizaciones.application.generar_pdf import GenerarPdf, GenerarPdfProyecto
from src.features.cotizaciones.application.listar_pdfs import ListarMisPdfs
from src.features.cotizaciones.application.listar_productos import (
    ListarProductosCercanos,
)
from src.features.extracciones.application.validar_extraccion import ValidarExtraccion
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
        session=session,
        merma=settings.cotizacion_merma,
    )


def get_crear_kit(
    session: AsyncSession = Depends(get_session),
) -> CrearCotizacionKit:
    return CrearCotizacionKit(
        repo=SqlAlchemyCotizacionRepository(session),
        proveedores=ProvidersAdapter(),
        session=session,
        merma=settings.cotizacion_merma,
    )


def get_generar_pdf(
    session: AsyncSession = Depends(get_session),
) -> GenerarPdf:
    return GenerarPdf(
        repo=SqlAlchemyCotizacionRepository(session),
        renderer=ReportLabPdfRenderer(),
    )


def get_listar_pdfs(
    session: AsyncSession = Depends(get_session),
) -> ListarMisPdfs:
    return ListarMisPdfs(repo=SqlAlchemyCotizacionRepository(session))


def get_generar_borrador(
    session: AsyncSession = Depends(get_session),
) -> GenerarBorradorCotizacion:
    return GenerarBorradorCotizacion(
        repo=SqlAlchemyCotizacionRepository(session),
        proveedores=ProvidersAdapter(),
        validar=ValidarExtraccion(),
        session=session,
        radio_km_default=settings.providers_radio_km_default,
        merma=settings.cotizacion_merma,
    )


def get_generar_pdf_proyecto(
    session: AsyncSession = Depends(get_session),
) -> GenerarPdfProyecto:
    return GenerarPdfProyecto(
        repo=SqlAlchemyCotizacionRepository(session),
        renderer=ReportLabPdfRenderer(),
        session=session,
    )
