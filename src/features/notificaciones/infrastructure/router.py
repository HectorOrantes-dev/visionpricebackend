"""Router de notificaciones.

- Usuario (JWT): ver su feed y marcar como leída.
- Interno (X-Api-Key): job de vencimientos + emitir eventos de negocio.
"""
from fastapi import APIRouter, Depends, status

from src.features.notificaciones.application.consultar import (
    ListarNotificaciones,
    MarcarLeida,
    MarcarLeidaCommand,
)
from src.features.notificaciones.application.emitir_evento import (
    EmitirEvento,
    EventoCommand,
)
from src.features.notificaciones.application.generar_vencimientos import (
    GenerarNotificacionesVencimiento,
)
from src.features.notificaciones.infrastructure.dependencies import (
    get_emitir_evento,
    get_generar_vencimientos,
    get_listar_notificaciones,
    get_marcar_leida,
)
from src.features.notificaciones.infrastructure.schemas import (
    EventoRequest,
    JobResultOut,
    NotificacionOut,
    OkOut,
)
from src.oauth.dependencies import CurrentUser, get_current_user
from src.oauth.internal import require_internal_key

router = APIRouter(tags=["notificaciones"])


@router.get(
    "/notificaciones",
    response_model=list[NotificacionOut],
    summary="Feed de notificaciones del usuario autenticado",
)
async def listar(
    no_leidas: bool = False,
    user: CurrentUser = Depends(get_current_user),
    use_case: ListarNotificaciones = Depends(get_listar_notificaciones),
) -> list[NotificacionOut]:
    items = await use_case.execute(user.id, solo_no_leidas=no_leidas)
    return [NotificacionOut(**n.__dict__) for n in items]


@router.post(
    "/notificaciones/{notificacion_id}/leida",
    response_model=OkOut,
    summary="Marcar una notificación como leída",
)
async def marcar_leida(
    notificacion_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: MarcarLeida = Depends(get_marcar_leida),
) -> OkOut:
    await use_case.execute(
        MarcarLeidaCommand(notificacion_id=notificacion_id, usuario_id=user.id)
    )
    return OkOut()


@router.post(
    "/notificaciones/jobs/vencimientos",
    response_model=JobResultOut,
    dependencies=[Depends(require_internal_key)],
    summary="Job (cron): generar avisos de suscripciones por vencer/vencidas",
)
async def job_vencimientos(
    use_case: GenerarNotificacionesVencimiento = Depends(get_generar_vencimientos),
) -> JobResultOut:
    res = await use_case.execute()
    return JobResultOut(por_vencer=res.por_vencer, vencidas=res.vencidas)


@router.post(
    "/notificaciones/eventos",
    response_model=NotificacionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_internal_key)],
    summary="Emitir una notificación de negocio (la usan otras features/microservicios)",
)
async def emitir_evento(
    body: EventoRequest,
    use_case: EmitirEvento = Depends(get_emitir_evento),
) -> NotificacionOut:
    notif = await use_case.execute(
        EventoCommand(
            usuario_id=body.usuario_id,
            tipo=body.tipo,
            titulo=body.titulo,
            cuerpo=body.cuerpo,
            referencia_tipo=body.referencia_tipo,
            referencia_id=body.referencia_id,
        )
    )
    return NotificacionOut(**notif.__dict__)
