"""Errores de dominio y formato uniforme de error.

Mismo contrato que tus microservicios:

    { "error": { "code": "...", "message": "..." } }

Las features lanzan `DomainError` (o subclases); `register_error_handlers`
los traduce a JSON con el status HTTP correcto.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_log = logging.getLogger("visionprice.errors")


class DomainError(Exception):
    """Error de negocio con código estable y status HTTP asociado."""

    code: str = "error"
    status_code: int = 400

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class Unauthorized(DomainError):
    code = "unauthorized"
    status_code = 401


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    status_code = 401


class Forbidden(DomainError):
    code = "forbidden"
    status_code = 403


class NotFound(DomainError):
    code = "not_found"
    status_code = 404


class Conflict(DomainError):
    code = "conflict"
    status_code = 409


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class TwoFactorRequired(DomainError):
    code = "two_factor_required"
    status_code = 401


class TwoFactorInvalid(DomainError):
    code = "two_factor_invalid"
    status_code = 401


class CodigoInvalido(DomainError):
    code = "code_invalid"
    status_code = 400


class CodigoExpirado(DomainError):
    code = "code_expired"
    status_code = 410


class NoActiveChallenge(DomainError):
    code = "no_active_challenge"
    status_code = 400


class TooManyAttempts(DomainError):
    code = "too_many_attempts"
    status_code = 429


class TooManyRequests(DomainError):
    code = "too_many_requests"
    status_code = 429


class UpstreamError(DomainError):
    """Falla al hablar con un microservicio externo."""

    code = "upstream_error"
    status_code = 502


class PlanLimiteAlcanzado(DomainError):
    """Se agotó el uso gratuito de un recurso (ver src/shared/plan_limites.py).

    402 (no 403): así el cliente distingue "no tienes permiso" (rol) de
    "necesitas pagar para seguir" sin tener que parsear el mensaje.
    """

    code = "plan_limit_reached"
    status_code = 402


class PlanRequerido(DomainError):
    """Función exclusiva de planes de pago, sin cuota gratis."""

    code = "plan_required"
    status_code = 402


class ProyectoLimiteAlcanzado(DomainError):
    """Tope fijo de cotizaciones/PDFs de un PROYECTO (no de un usuario).

    409 (no 402): a diferencia de PlanLimiteAlcanzado, pagar no lo
    desbloquea — es un tope duro del proyecto compartido, ver
    src/shared/proyecto_limites.py.
    """

    code = "project_limit_reached"
    status_code = 409


def _payload(code: str, message: str, details: dict | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        # Loguea los 5xx (p. ej. upstream_error) para verlos en Railway.
        if exc.status_code >= 500:
            _log.warning(
                "%s %s -> %s: %s | details=%s",
                request.method,
                request.url.path,
                exc.code,
                exc.message,
                exc.details,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # exc.errors() puede traer una Exception en ctx (validadores custom),
        # que no es serializable a JSON: la convertimos a str.
        errores = []
        for e in exc.errors():
            e = dict(e)
            ctx = e.get("ctx")
            if ctx:
                e["ctx"] = {
                    k: (str(v) if isinstance(v, Exception) else v)
                    for k, v in ctx.items()
                }
            errores.append(e)
        return JSONResponse(
            status_code=422,
            content=_payload(
                "validation_error",
                "Datos de entrada inválidos.",
                {"errors": jsonable_encoder(errores)},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload("http_error", str(exc.detail)),
        )
