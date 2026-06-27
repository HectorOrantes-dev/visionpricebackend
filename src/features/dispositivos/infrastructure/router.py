"""Router de dispositivos: la app móvil registra/borra su device token (JWT)."""
from fastapi import APIRouter, Depends, status

from src.features.dispositivos.application.gestionar_dispositivo import (
    EliminarDispositivo,
    EliminarDispositivoCommand,
    RegistrarDispositivo,
    RegistrarDispositivoCommand,
)
from src.features.dispositivos.infrastructure.dependencies import (
    get_eliminar_dispositivo,
    get_registrar_dispositivo,
)
from src.features.dispositivos.infrastructure.schemas import (
    EliminarDispositivoRequest,
    OkOut,
    RegistrarDispositivoRequest,
)
from src.oauth.dependencies import CurrentUser, get_current_user

router = APIRouter(tags=["dispositivos"])


@router.post(
    "/dispositivos",
    response_model=OkOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el device token FCM del usuario (la app lo llama al loguear)",
)
async def registrar(
    body: RegistrarDispositivoRequest,
    user: CurrentUser = Depends(get_current_user),
    use_case: RegistrarDispositivo = Depends(get_registrar_dispositivo),
) -> OkOut:
    await use_case.execute(
        RegistrarDispositivoCommand(
            usuario_id=user.id, token=body.token, plataforma=body.plataforma
        )
    )
    return OkOut()


@router.delete(
    "/dispositivos",
    response_model=OkOut,
    summary="Eliminar un device token (logout / desinstalación)",
)
async def eliminar(
    body: EliminarDispositivoRequest,
    user: CurrentUser = Depends(get_current_user),
    use_case: EliminarDispositivo = Depends(get_eliminar_dispositivo),
) -> OkOut:
    await use_case.execute(
        EliminarDispositivoCommand(usuario_id=user.id, token=body.token)
    )
    return OkOut()
