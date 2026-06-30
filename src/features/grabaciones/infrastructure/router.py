"""Router de grabaciones: alta de audio + consulta (estado/transcripción) + webhook ML."""
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.features.grabaciones.application.consultar_grabaciones import (
    ListarGrabaciones,
    ObtenerGrabacion,
)
from src.features.grabaciones.application.procesar_resultado_ml import (
    ProcesarResultadoML,
)
from src.features.grabaciones.application.registrar_grabacion import (
    RegistrarGrabacion,
    RegistrarGrabacionCommand,
)
from src.features.grabaciones.domain.entities import ResultadoML
from src.features.grabaciones.infrastructure.dependencies import (
    get_listar_grabaciones,
    get_obtener_grabacion,
    get_procesar_resultado_ml,
    get_registrar_grabacion,
)
from src.features.grabaciones.infrastructure.schemas import (
    GrabacionDetalleOut,
    GrabacionOut,
    GrabacionResumenOut,
    MLCallbackRequest,
    MLCallbackResponse,
)
from src.oauth.dependencies import CurrentUser, get_current_user
from src.oauth.internal import require_internal_key

router = APIRouter(tags=["grabaciones"])


@router.get(
    "/grabaciones",
    response_model=list[GrabacionResumenOut],
    summary="Historial de mis grabaciones (con estado de sincronización)",
)
async def listar_grabaciones(
    user: CurrentUser = Depends(get_current_user),
    use_case: ListarGrabaciones = Depends(get_listar_grabaciones),
) -> list[GrabacionResumenOut]:
    items = await use_case.execute(user.id)
    return [GrabacionResumenOut(**g.__dict__) for g in items]


@router.get(
    "/grabaciones/{grabacion_id}",
    response_model=GrabacionDetalleOut,
    summary="Detalle: estado + transcripción + extracción (cuando esté lista)",
)
async def obtener_grabacion(
    grabacion_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: ObtenerGrabacion = Depends(get_obtener_grabacion),
) -> GrabacionDetalleOut:
    detalle = await use_case.execute(grabacion_id, user.id)
    return GrabacionDetalleOut(**detalle.__dict__)


@router.post(
    "/grabaciones",
    response_model=GrabacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una grabación: guarda metadata y la envía al microservicio ML",
)
async def crear_grabacion(
    proyecto_id: int = Form(..., description="Obligatorio: el micro de ML lo exige"),
    duracion_segundos: int | None = Form(default=None),
    audio: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    use_case: RegistrarGrabacion = Depends(get_registrar_grabacion),
) -> GrabacionOut:
    contenido = await audio.read()
    grabacion = await use_case.execute(
        RegistrarGrabacionCommand(
            usuario_id=user.id,
            user_hash=str(user.id),
            proyecto_id=proyecto_id,
            filename=audio.filename or "audio.wav",
            content_type=audio.content_type or "application/octet-stream",
            audio=contenido,
            duracion_segundos=duracion_segundos,
        )
    )
    return GrabacionOut(
        id=grabacion.id,
        usuario_id=grabacion.usuario_id,
        proyecto_id=grabacion.proyecto_id,
        object_storage_key=grabacion.object_storage_key,
        estado_sincronizacion=grabacion.estado_sincronizacion,
    )


@router.post(
    "/ml/callback",
    response_model=MLCallbackResponse,
    dependencies=[Depends(require_internal_key)],
    summary="Webhook: el microservicio de ML entrega transcripción + extracción",
)
async def ml_callback(
    body: MLCallbackRequest,
    use_case: ProcesarResultadoML = Depends(get_procesar_resultado_ml),
) -> MLCallbackResponse:
    await use_case.execute(
        ResultadoML(
            grabacion_id=body.grabacion_id,
            texto=body.texto,
            parametros_json=body.parametros_json,
            object_storage_key=body.object_storage_key,
            modelo_voice_to_text=body.modelo_voice_to_text,
            confianza=body.confianza,
            version_modelo=body.version_modelo,
        )
    )
    return MLCallbackResponse(received=True, grabacion_id=body.grabacion_id)
