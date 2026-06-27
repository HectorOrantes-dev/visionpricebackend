"""Middleware de idempotencia.

Se activa SOLO para peticiones mutantes (POST/PUT/PATCH) que traigan el header
`Idempotency-Key`. Con la misma llave:
  - 1ª vez: procesa, guarda la respuesta y la devuelve.
  - repeticiones (doble-click): devuelve la respuesta guardada SIN reprocesar.
  - en curso (concurrente): 409 (ya se está procesando).
  - misma llave con body distinto: 409 (uso indebido de la llave).

Es genérico: la app decide qué peticiones proteger enviando el header (típico:
pagos, crear cotización). Si falla la infraestructura de idempotencia, NO se
bloquea la petición (fail-open) — solo se pierde la protección en ese caso.
"""
import base64
import hashlib
import json
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core.database import SessionLocal
from src.shared.models import IdempotencyKey
from src.shared.security import decode_access_token
from src.shared.timeutils import utcnow

_log = logging.getLogger("idempotency")
_MUTANTES = {"POST", "PUT", "PATCH"}


def _header(scope, nombre: bytes) -> bytes | None:
    for k, v in scope["headers"]:
        if k == nombre:
            return v
    return None


def _usuario_id(scope) -> int | None:
    auth = _header(scope, b"authorization")
    if not auth or not auth.startswith(b"Bearer "):
        return None
    try:
        payload = decode_access_token(auth[7:].decode())
        return int(payload["sub"])
    except Exception:  # noqa: BLE001
        return None


async def _leer_body(receive) -> bytes:
    body = b""
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        else:
            break
    return body


def _replay_receive(body: bytes):
    enviado = {"done": False}

    async def receive():
        if enviado["done"]:
            return {"type": "http.disconnect"}
        enviado["done"] = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


async def _send_json(send, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class IdempotencyMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in _MUTANTES:
            return await self.app(scope, receive, send)

        clave_b = _header(scope, b"idempotency-key")
        if not clave_b:
            return await self.app(scope, receive, send)

        clave = clave_b.decode()
        body = await _leer_body(receive)
        req_hash = hashlib.sha256(scope["path"].encode() + b"|" + body).hexdigest()
        receive = _replay_receive(body)

        try:
            return await self._con_idempotencia(
                scope, receive, send, clave, req_hash, body
            )
        except Exception as exc:  # noqa: BLE001 — fail-open: no romper la petición
            _log.warning("Idempotencia deshabilitada por error: %s", exc)
            return await self.app(scope, receive, send)

    async def _con_idempotencia(self, scope, receive, send, clave, req_hash, body):
        async with SessionLocal() as session:
            registro = IdempotencyKey(
                clave=clave,
                usuario_id=_usuario_id(scope),
                metodo=scope["method"],
                ruta=scope["path"],
                request_hash=req_hash,
                estado="procesando",
            )
            session.add(registro)
            try:
                await session.commit()
                primera_vez = True
            except IntegrityError:
                await session.rollback()
                primera_vez = False

            if not primera_vez:
                existente = (
                    await session.execute(
                        select(IdempotencyKey).where(IdempotencyKey.clave == clave)
                    )
                ).scalar_one()
                if existente.request_hash != req_hash:
                    return await _send_json(
                        send,
                        409,
                        {"error": {"code": "idempotency_key_reuse",
                                   "message": "La llave de idempotencia se usó con otro cuerpo."}},
                    )
                if existente.estado != "completado":
                    return await _send_json(
                        send,
                        409,
                        {"error": {"code": "request_in_progress",
                                   "message": "La petición ya se está procesando."}},
                    )
                # Repetición: devolver la respuesta guardada sin reprocesar.
                cuerpo = base64.b64decode(existente.response_body or "")
                await send(
                    {
                        "type": "http.response.start",
                        "status": existente.status_code or 200,
                        "headers": [
                            (b"content-type",
                             (existente.content_type or "application/json").encode()),
                            (b"idempotent-replay", b"true"),
                        ],
                    }
                )
                return await send({"type": "http.response.body", "body": cuerpo})

        # Primera vez: ejecutar la app capturando la respuesta.
        captura = {"status": 200, "body": b"", "content_type": "application/json"}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                captura["status"] = message["status"]
                for k, v in message.get("headers", []):
                    if k == b"content-type":
                        captura["content_type"] = v.decode()
            elif message["type"] == "http.response.body":
                captura["body"] += message.get("body", b"")
            await send(message)

        await self.app(scope, receive, send_wrapper)

        # Guardar la respuesta (solo si no fue error de servidor).
        async with SessionLocal() as session:
            existente = (
                await session.execute(
                    select(IdempotencyKey).where(IdempotencyKey.clave == clave)
                )
            ).scalar_one_or_none()
            if existente is None:
                return
            if captura["status"] < 500:
                existente.estado = "completado"
                existente.status_code = captura["status"]
                existente.content_type = captura["content_type"]
                existente.response_body = base64.b64encode(captura["body"]).decode()
                existente.fecha_actualizacion = utcnow()
            else:
                # error de servidor: borrar para permitir reintento
                await session.delete(existente)
            await session.commit()
