"""Router HTTP de la feature login (2 pasos: credenciales + 2FA)."""
from fastapi import APIRouter, Depends, Request, status

from src.features.login.application.authenticate_user import (
    AuthenticateUser,
    LoginCommand,
)
from src.features.login.application.verify_two_factor import (
    VerifyCommand,
    VerifyTwoFactor,
)
from src.features.login.infrastructure.dependencies import (
    get_authenticate_user,
    get_verify_two_factor,
)
from src.features.login.infrastructure.schemas import (
    LoginChallengeOut,
    LoginRequest,
    TokenOut,
    VerifyRequest,
)
from src.shared.request_utils import get_client_ip

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginChallengeOut,
    status_code=status.HTTP_200_OK,
    summary="Paso 1: validar credenciales y enviar código 2FA",
)
async def login(
    body: LoginRequest,
    request: Request,
    use_case: AuthenticateUser = Depends(get_authenticate_user),
) -> LoginChallengeOut:
    challenge = await use_case.execute(
        LoginCommand(
            correo=body.correo,
            contrasena=body.contrasena,
            ip_origen=get_client_ip(request),
        )
    )
    return LoginChallengeOut(
        correo=challenge.correo,
        two_factor_sent=challenge.two_factor_sent,
        message="Credenciales correctas. Te enviamos un código a tu correo.",
    )


@router.post(
    "/login/verify",
    response_model=TokenOut,
    status_code=status.HTTP_200_OK,
    summary="Paso 2: verificar código 2FA y emitir JWT",
)
async def verify(
    body: VerifyRequest,
    use_case: VerifyTwoFactor = Depends(get_verify_two_factor),
) -> TokenOut:
    token = await use_case.execute(
        VerifyCommand(correo=body.correo, code=body.code)
    )
    return TokenOut(
        access_token=token.access_token,
        token_type=token.token_type,
        user_id=token.user_id,
        correo=token.correo,
        rol=token.rol,
    )
