"""Router HTTP de la feature register."""
from fastapi import APIRouter, Depends, status

from src.features.register.application.register_user import (
    RegisterUser,
    RegisterUserCommand,
)
from src.features.register.infrastructure.dependencies import get_register_user
from src.features.register.infrastructure.schemas import (
    RegisteredUserOut,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario y enviar código 2FA",
)
async def register(
    body: RegisterRequest,
    use_case: RegisterUser = Depends(get_register_user),
) -> RegisterResponse:
    user = await use_case.execute(
        RegisterUserCommand(
            nombre=body.nombre,
            correo=body.correo,
            contrasena=body.contrasena,
            rol=body.rol,
            telefono=body.telefono,
        ),
        send_2fa=True,
    )
    return RegisterResponse(
        usuario=RegisteredUserOut(
            id=user.id,
            nombre=user.nombre,
            correo=user.correo,
            telefono=user.telefono,
            rol=user.rol,
            activo=user.activo,
            fecha_registro=user.fecha_registro,
        ),
        two_factor_sent=True,
        message="Usuario registrado. Revisa tu correo para el código de verificación.",
    )
