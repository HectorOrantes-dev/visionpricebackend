"""Router de cotizaciones (todo protegido con JWT del usuario)."""
from io import BytesIO

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse

from src.core.config import settings
from src.features.cotizaciones.application.calcular_areas import (
    CalcularAreas,
    CalcularAreasCommand,
)
from src.features.cotizaciones.application.crear_cotizacion import (
    CrearCotizacion,
    CrearCotizacionCommand,
    ItemSeleccionado,
)
from src.features.cotizaciones.application.crear_kit import (
    CrearCotizacionKit,
    CrearKitCommand,
    SuperficieKit,
)
from src.features.cotizaciones.application.generar_borrador import (
    GenerarBorradorCotizacion,
    GenerarBorradorCommand,
)
from src.features.cotizaciones.application.generar_pdf import GenerarPdf, GenerarPdfProyecto
from src.features.cotizaciones.application.listar_pdfs import ListarMisPdfs
from src.features.cotizaciones.application.listar_productos import (
    ListarProductosCercanos,
    ProductosCercanosQuery,
)
from src.features.cotizaciones.infrastructure.dependencies import (
    get_calcular_areas,
    get_crear_cotizacion,
    get_crear_kit,
    get_generar_borrador,
    get_generar_pdf,
    get_generar_pdf_proyecto,
    get_listar_pdfs,
    get_listar_productos,
)
from src.features.cotizaciones.domain.reglas_material import todas as reglas_todas
from src.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.plan_limites import (
    obtener_uso_cotizaciones,
    verificar_limite_cotizaciones,
)
from src.features.recomendaciones.infrastructure.dependencies import (
    get_recomendacion_uso_repository,
)
from src.features.recomendaciones.infrastructure.repository import (
    SqlAlchemyRecomendacionUsoRepository,
)
from src.features.cotizaciones.infrastructure.schemas import (
    BorradorOut,
    BorradorRequest,
    CalculoOut,
    CalculoRequest,
    CotizacionOut,
    CotizacionPdfOut,
    CrearCotizacionRequest,
    CrearKitRequest,
    MaterialReglaOut,
    ProductoCercanoOut,
    UsoCotizacionesOut,
)
from src.oauth.dependencies import CurrentUser, get_current_user
from src.oauth.permisos import Permisos
from src.oauth.roles import require_roles
from src.shared.auditoria import Auditor, get_auditor
from src.shared.request_utils import get_client_ip

# Cotizar (calcular, ver productos, crear cotización, PDF) lo hacen TODOS los roles.
router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])


@router.get(
    "/materiales",
    response_model=list[MaterialReglaOut],
    summary="Reglas por material: si es simple (rendimiento) o kit + complementos",
)
async def materiales(
    _: CurrentUser = Depends(get_current_user),
) -> list[MaterialReglaOut]:
    return [MaterialReglaOut(**r.__dict__) for r in reglas_todas()]


@router.post(
    "/calculo",
    response_model=CalculoOut,
    summary="Calcular m² de piso y paredes desde la transcripción o un texto",
)
async def calcular(
    body: CalculoRequest,
    _: CurrentUser = Depends(get_current_user),
    use_case: CalcularAreas = Depends(get_calcular_areas),
) -> CalculoOut:
    areas = await use_case.execute(
        CalcularAreasCommand(
            grabacion_id=body.grabacion_id,
            texto=body.texto,
            largo_m=body.largo_m,
            ancho_m=body.ancho_m,
            alto_m=body.alto_m,
            piso_m2=body.piso_m2,
            paredes_m2=body.paredes_m2,
        )
    )
    return CalculoOut(**areas.__dict__)


@router.get(
    "/productos",
    response_model=list[ProductoCercanoOut],
    summary="Productos de proveedores cercanos a la ubicación del usuario",
)
async def productos_cercanos(
    lat: float = Query(...),
    lng: float = Query(...),
    radio_km: float | None = Query(default=None),
    categoria: str | None = Query(default=None),
    _: CurrentUser = Depends(get_current_user),
    use_case: ListarProductosCercanos = Depends(get_listar_productos),
) -> list[ProductoCercanoOut]:
    productos = await use_case.execute(
        ProductosCercanosQuery(
            lat=lat,
            lng=lng,
            radio_km=radio_km or settings.providers_radio_km_default,
            categoria=categoria,
        )
    )
    return [ProductoCercanoOut(**p.__dict__) for p in productos]


@router.post(
    "/borrador",
    response_model=BorradorOut,
    summary=(
        "Borrador automático: toma la extracción de una grabación, empareja "
        "proveedores cercanos y arma una cotización pre-llenada para confirmar"
    ),
    dependencies=[Depends(require_roles(*Permisos.COTIZAR))],
)
async def borrador(
    body: BorradorRequest,
    user: CurrentUser = Depends(verificar_limite_cotizaciones),
    use_case: GenerarBorradorCotizacion = Depends(get_generar_borrador),
) -> BorradorOut:
    resultado = await use_case.execute(
        GenerarBorradorCommand(
            grabacion_id=body.grabacion_id,
            usuario_id=user.id,
            superficies_manual=(
                [s.model_dump() for s in body.superficies]
                if body.superficies
                else None
            ),
        )
    )
    return BorradorOut(
        proyecto_id=resultado.proyecto_id,
        grabacion_id=resultado.grabacion_id,
        superficies=[
            {
                "categoria": s.categoria,
                "descripcion": s.descripcion,
                "area_m2": s.area_m2,
                "metodo": s.metodo,
                "lineas": [ln.__dict__ for ln in s.lineas],
            }
            for s in resultado.superficies
        ],
        total_estimado=resultado.total_estimado,
        advertencias=resultado.advertencias,
        cuerpo_confirmacion=resultado.cuerpo_confirmacion,
    )


@router.post(
    "",
    response_model=CotizacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cotización con los productos elegidos",
    dependencies=[Depends(require_roles(*Permisos.COTIZAR))],
)
async def crear(
    body: CrearCotizacionRequest,
    request: Request,
    user: CurrentUser = Depends(verificar_limite_cotizaciones),
    use_case: CrearCotizacion = Depends(get_crear_cotizacion),
    auditor: Auditor = Depends(get_auditor),
) -> CotizacionOut:
    cot = await use_case.execute(
        CrearCotizacionCommand(
            proyecto_id=body.proyecto_id,
            usuario_id=user.id,
            piso_m2=body.piso_m2,
            paredes_m2=body.paredes_m2,
            items=[
                ItemSeleccionado(
                    producto_id=i.producto_id,
                    area_m2=i.area_m2,
                    aplicar_a=i.aplicar_a,
                    descripcion=i.descripcion,
                )
                for i in body.items
            ],
            mano_obra=body.mano_obra,
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="cotizacion_creada",
        tabla_afectada="presupuestos",
        registro_id=cot.id,
        detalles={"total": cot.total, "proyecto_id": cot.proyecto_id},
        ip_origen=get_client_ip(request),
    )
    return CotizacionOut(
        id=cot.id,
        numero=cot.numero,
        proyecto_id=cot.proyecto_id,
        estado=cot.estado,
        total=cot.total,
        fecha=cot.fecha,
        mano_obra=cot.mano_obra,
        lineas=[ln.__dict__ for ln in cot.lineas],
    )


@router.post(
    "/kit",
    response_model=CotizacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cotización tipo KIT (loseta + pegazulejo + crucetas + boquilla)",
    dependencies=[Depends(require_roles(*Permisos.COTIZAR))],
)
async def crear_kit(
    body: CrearKitRequest,
    request: Request,
    user: CurrentUser = Depends(verificar_limite_cotizaciones),
    use_case: CrearCotizacionKit = Depends(get_crear_kit),
    auditor: Auditor = Depends(get_auditor),
    recomendaciones_repo: SqlAlchemyRecomendacionUsoRepository = Depends(
        get_recomendacion_uso_repository
    ),
) -> CotizacionOut:
    cot = await use_case.execute(
        CrearKitCommand(
            proyecto_id=body.proyecto_id,
            usuario_id=user.id,
            superficies=[
                SuperficieKit(
                    area_m2=s.area_m2,
                    principal_producto_id=s.principal_producto_id,
                    descripcion=s.descripcion,
                    metodo_crucetas=s.metodo_crucetas,
                    adhesivo_producto_id=s.adhesivo_producto_id,
                    cruceta_producto_id=s.cruceta_producto_id,
                    boquilla_producto_id=s.boquilla_producto_id,
                )
                for s in body.superficies
            ],
            mano_obra=body.mano_obra,
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="cotizacion_kit_creada",
        tabla_afectada="presupuestos",
        registro_id=cot.id,
        detalles={"total": cot.total, "proyecto_id": cot.proyecto_id},
        ip_origen=get_client_ip(request),
    )
    if body.recomendacion_id is not None:
        # No crítico: si el id no existe o ya se usó, no se rompe la
        # creación de la cotización — solo se pierde ese dato de auditoría.
        await recomendaciones_repo.marcar_usada(body.recomendacion_id, cot.id)
    return CotizacionOut(
        id=cot.id,
        numero=cot.numero,
        proyecto_id=cot.proyecto_id,
        estado=cot.estado,
        total=cot.total,
        fecha=cot.fecha,
        mano_obra=cot.mano_obra,
        lineas=[ln.__dict__ for ln in cot.lineas],
    )


@router.get(
    "/uso",
    response_model=UsoCotizacionesOut,
    summary="Cuántas cotizaciones lleva el usuario y cuántas le quedan del plan gratuito",
)
async def uso(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UsoCotizacionesOut:
    uso = await obtener_uso_cotizaciones(session, user.id)
    return UsoCotizacionesOut(**uso.__dict__)


@router.get(
    "/pdfs",
    response_model=list[CotizacionPdfOut],
    summary="Listar todos los PDFs (cotizaciones) creadas por el usuario, en todas sus obras",
)
async def mis_pdfs(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    use_case: ListarMisPdfs = Depends(get_listar_pdfs),
) -> list[CotizacionPdfOut]:
    items = await use_case.execute(user.id)
    return [
        CotizacionPdfOut(
            id=it.id,
            numero=it.numero,
            proyecto_id=it.proyecto_id,
            proyecto_nombre=it.proyecto_nombre,
            estado=it.estado,
            total=it.total,
            fecha=it.fecha,
            url_pdf=str(request.url_for("pdf", cotizacion_id=it.id)),
        )
        for it in items
    ]


@router.get(
    "/{cotizacion_id}/pdf",
    summary="Descargar el PDF de la cotización (generado al vuelo)",
)
async def pdf(
    cotizacion_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: GenerarPdf = Depends(get_generar_pdf),
) -> StreamingResponse:
    contenido = await use_case.execute(cotizacion_id, user.id)
    return StreamingResponse(
        BytesIO(contenido),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cotizacion_{cotizacion_id}.pdf"'
        },
    )


@router.get(
    "/proyecto/{proyecto_id}/pdf",
    summary="Descargar el PDF con todas las cotizaciones de un proyecto",
)
async def pdf_proyecto(
    proyecto_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: GenerarPdfProyecto = Depends(get_generar_pdf_proyecto),
) -> StreamingResponse:
    contenido = await use_case.execute(proyecto_id, user.id)
    return StreamingResponse(
        BytesIO(contenido),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="proyecto_{proyecto_id}_cotizaciones.pdf"'
        },
    )
