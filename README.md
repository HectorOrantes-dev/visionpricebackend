# VisionPrice — API principal (Módulo de Usuarios)

API en **FastAPI** con **arquitectura hexagonal**, **SQLAlchemy async** + **Alembic**.
Emite el JWT (HS256) que validan los microservicios, e integra el microservicio **2FA**
en el flujo de login. Base de datos: el esquema del `.sql` (11 tablas, PostgreSQL 16).

## Arranque local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ajusta JWT_SECRET y las URLs de microservicios
alembic upgrade head          # crea las tablas + seed de roles (SQLite local)
uvicorn main:app --reload
```

Swagger: http://localhost:8000/docs · Health: http://localhost:8000/health

## Endpoints

| Método | Ruta                          | Auth        | Descripción                              |
|--------|-------------------------------|-------------|------------------------------------------|
| GET    | `/health`                     | ❌          | Liveness                                 |
| POST   | `/api/v1/auth/register`       | ❌          | Crea usuario + envía código 2FA          |
| POST   | `/api/v1/auth/login`          | ❌          | Paso 1: valida credenciales, envía 2FA   |
| POST   | `/api/v1/auth/login/verify`   | ❌          | Paso 2: valida código 2FA → emite JWT    |
| GET    | `/api/v1/me`                  | 🔒 Bearer   | Identidad del usuario (desde el JWT)     |
| GET    | `/api/v1/me/subscriptions`    | 🔒 Bearer   | Proxy al microservicio de Pagos          |
| POST   | `/api/v1/grabaciones`         | 🔒 Bearer   | Sube audio: guarda metadata y lo manda al micro de ML |
| POST   | `/api/v1/ml/callback`         | 🔑 X-Api-Key | Webhook: el micro de ML entrega transcripción + extracción |
| POST   | `/api/v1/pagos/callback`      | 🔑 X-Api-Key | Webhook: el micro de Pagos sincroniza el plan del usuario |

🔑 = autenticación servicio-a-servicio con `X-Api-Key: <WEBHOOK_API_KEY>` (callbacks entrantes).

### Flujo de audio (ML)
```
App → POST /grabaciones (audio, proyecto_id)   API guarda metadata (estado=pendiente)
API → micro ML: sube el audio (grabacion_id)   ML guarda el binario en object storage
ML procesa async → POST /ml/callback           API rellena transcripciones + extracciones_llm (estado=sincronizado)
```
El **binario** vive en el object storage del micro de ML; la API principal sólo guarda
la referencia (`object_storage_key`) + metadatos, y el **resultado** que necesita para presupuestos.

### Flujo de pagos (entitlement)
El micro de Pagos es dueño de la facturación. Cuando cambia una suscripción, llama a
`POST /pagos/callback` y la API principal cachea sólo `usuarios.plan_activo` + `vigencia_hasta`
para autorizar rápido sin depender de Pagos en cada request.

### Desafíos 2FA
Cada login crea un registro en `desafios_2fa` (estado, intentos, IP) — el **código** lo
sigue guardando/validando el micro de 2FA; esta tabla es sólo para auditoría y rate-limiting.

Flujo de login: `login` → el usuario recibe el código por correo → `login/verify` con el
código → se devuelve `access_token`. Ese token se manda como `Authorization: Bearer <JWT>`
y es el mismo que valida el microservicio de Pagos (comparten `JWT_SECRET`).

## Estructura (hexagonal)

```
main.py                       App factory (routers, CORS, errores, /health)
src/core/                     config (env) · database (engine async)
src/shared/                   models (11 tablas) · errors · security (hash + JWT) · schemas
src/oauth/                    validación del JWT entrante → get_current_user
src/features/
  register/  login/           domain (entities/ports) · application (use cases) · infrastructure (repo/router/schemas/DI)
  two_factor/                 puerto + adaptador httpx al microservicio 2FA
  account/                    rutas protegidas de ejemplo (/me, proxy Pagos)
  proyectos/ grabaciones/ transcripciones/ extracciones/
  presupuestos/ documentos/ auditoria/      scaffold listo para implementar
src/microservices/            gateways: payments_gateway (Bearer) · extractions_gateway (X-Api-Key)
alembic/                      env.py + migración 0001 (las 11 tablas + seed roles)
Dockerfile                    migra y arranca (Railway: usa $PORT)
```

### Cómo agregar una feature nueva (ej. `proyectos`)
1. `domain/`: entidades + `ports.py` (interfaz del repositorio).
2. `application/`: el/los caso(s) de uso usando esos puertos.
3. `infrastructure/`: `repository.py` (SQLAlchemy sobre `src/shared/models.py`),
   `schemas.py`, `dependencies.py` (DI) y `router.py`.
4. Monta el router en `main.py` con `prefix=settings.api_prefix`.
   Protégelo con `Depends(get_current_user)`.

## Despliegue en Railway + Neon

### 1. Base de datos (Neon)
1. Crea un proyecto en [Neon](https://neon.tech) y copia la **Connection string**.
2. **Opción A (recomendada): deja que Alembic cree el esquema.** No hagas nada en Neon;
   el deploy ejecuta `alembic upgrade head` y crea las 12 tablas + seed de roles.
3. **Opción B: cargar el `.sql` a mano.** Abre el *SQL Editor* de Neon, pega el contenido
   de [`.sql`](.sql) y ejecútalo. Ya incluye el *stamp* de Alembic, así que el deploy
   detecta el esquema como actualizado y no lo recrea.

> No mezcles las dos opciones en la misma base: si corres el `.sql`, no necesitas migrar.

### 2. App (Railway)
1. Crea un servicio en Railway desde este repo. Detecta el [`Dockerfile`](Dockerfile)
   y usa [`railway.json`](railway.json) (healthcheck en `/health`).
2. Configura las **variables de entorno** (Settings → Variables):

   | Variable | Valor |
   |----------|-------|
   | `DATABASE_URL` | La connection string de Neon (tal cual, con `?sslmode=require`) |
   | `JWT_SECRET` | Secreto largo — **el MISMO** que el microservicio de Pagos |
   | `WEBHOOK_API_KEY` | API key interna para los callbacks de ML y Pagos |
   | `TWO_FACTOR_BASE_URL` | URL del microservicio 2FA |
   | `EXTRACTIONS_BASE_URL` / `EXTRACTIONS_API_KEY` | Microservicio de extracciones |
   | `PAYMENTS_BASE_URL` | Microservicio de pagos |
   | `ALLOWED_ORIGINS` | Dominios del front separados por coma |
   | `ENVIRONMENT` | `production` |

3. **Genera el dominio público**: Settings → Networking → Generate Domain. Railway
   inyecta `PORT` automáticamente (no la pongas tú).
4. La URL del webhook que darás a los otros microservicios será
   `https://<tu-servicio>.up.railway.app/api/v1/ml/callback` (y `/pagos/callback`).

La normalización de la URL de Neon (driver `asyncpg` + SSL) la hace
[`src/core/config.py`](src/core/config.py); pegas la string de Neon sin tocarla.

## Microservicios integrados
- **2FA**: `TWO_FACTOR_BASE_URL` — `src/features/two_factor`.
- **Pagos**: `PAYMENTS_BASE_URL` — `src/microservices/payments_gateway.py` (reenvía el JWT).
- **Extracciones**: `EXTRACTIONS_BASE_URL` + `EXTRACTIONS_API_KEY` — `src/microservices/extractions_gateway.py`.
```
```
