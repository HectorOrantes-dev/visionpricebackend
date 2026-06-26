"""Router de login/register con Google."""
from fastapi import APIRouter, Depends, status

from src.features.google_auth.application.google_login import (
    GoogleLogin,
    GoogleLoginCommand,
)
from src.features.google_auth.application.google_register import (
    GoogleRegister,
    GoogleRegisterCommand,
)
from src.features.google_auth.infrastructure.dependencies import (
    get_google_login,
    get_google_register,
)
from src.features.google_auth.infrastructure.schemas import (
    GoogleLoginRequest,
    GoogleRegisterRequest,
    GoogleTokenOut,
)

router = APIRouter(prefix="/auth/google", tags=["auth-google"])


@router.post(
    "/login",
    response_model=GoogleTokenOut,
    summary="Login con Google (usuario existente) → JWT",
)
async def google_login(
    body: GoogleLoginRequest,
    use_case: GoogleLogin = Depends(get_google_login),
) -> GoogleTokenOut:
    token = await use_case.execute(GoogleLoginCommand(id_token=body.id_token))
    return GoogleTokenOut(**token.__dict__)


@router.post(
    "/register",
    response_model=GoogleTokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register con Google (requiere rol del selector) → JWT",
)
async def google_register(
    body: GoogleRegisterRequest,
    use_case: GoogleRegister = Depends(get_google_register),
) -> GoogleTokenOut:
    token = await use_case.execute(
        GoogleRegisterCommand(id_token=body.id_token, rol=body.rol)
    )
    return GoogleTokenOut(**token.__dict__)
