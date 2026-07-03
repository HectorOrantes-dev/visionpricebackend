"""Router de restablecimiento de contraseña (olvidé mi contraseña).

Flujo recomendado:
  1. POST /auth/password/forgot       → el micro 2FA envía el código al correo
  2. POST /auth/password/verify-code  → valida el código y devuelve reset_token
  3. POST /auth/password/reset        → con reset_token (o code) fija la nueva pass
"""
from fastapi import APIRouter, Depends, Request, status

from src.features.password.application.restablecer import (
    Restablecer,
    RestablecerCommand,
)
from src.features.password.application.solicitar_reset import SolicitarReset
from src.features.password.application.verificar_codigo import VerificarCodigo
from src.features.password.infrastructure.dependencies import (
    get_restablecer,
    get_solicitar_reset,
    get_verificar_codigo,
)
from src.features.password.infrastructure.schemas import (
    ForgotRequest,
    MessageOut,
    ResetRequest,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from src.shared.auditoria import Auditor, get_auditor
from src.shared.request_utils import get_client_ip

router = APIRouter(prefix="/auth/password", tags=["auth"])

# Mensaje genérico para no revelar si el correo existe (anti-enumeración).
_GENERICO = (
    "Si el correo está registrado, te enviamos un código para restablecer "
    "tu contraseña."
)


@router.post(
    "/forgot",
    response_model=MessageOut,
    summary="Olvidé mi contraseña: pide al micro 2FA que envíe el código",
)
async def forgot(
    body: ForgotRequest,
    use_case: SolicitarReset = Depends(get_solicitar_reset),
) -> MessageOut:
    await use_case.execute(body.correo)
    return MessageOut(message=_GENERICO)


@router.post(
    "/verify-code",
    response_model=VerifyCodeResponse,
    summary="Verifica el código y devuelve un reset_token de un solo uso",
)
async def verify_code(
    body: VerifyCodeRequest,
    use_case: VerificarCodigo = Depends(get_verificar_codigo),
) -> VerifyCodeResponse:
    reset_token = await use_case.execute(body.correo, body.code)
    return VerifyCodeResponse(valid=True, reset_token=reset_token)


@router.post(
    "/reset",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Fija la nueva contraseña (con reset_token o code)",
)
async def reset(
    body: ResetRequest,
    request: Request,
    use_case: Restablecer = Depends(get_restablecer),
    auditor: Auditor = Depends(get_auditor),
) -> MessageOut:
    usuario_id = await use_case.execute(
        RestablecerCommand(
            correo=body.correo,
            nueva_contrasena=body.nueva_contrasena,
            reset_token=body.reset_token,
            code=body.code,
        )
    )
    await auditor.registrar(
        usuario_id=usuario_id,
        accion="password_reset",
        tabla_afectada="usuarios",
        registro_id=usuario_id,
        ip_origen=get_client_ip(request),
    )
    return MessageOut(message="Contraseña actualizada. Ya puedes iniciar sesión.")
