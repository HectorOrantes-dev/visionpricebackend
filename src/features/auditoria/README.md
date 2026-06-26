# Feature: auditoria

Scaffold hexagonal listo para implementar. Sigue el mismo patrón que `register`/`login`:

- `domain/`         entidades + puertos (interfaces de repositorio/servicios). Sin dependencias de framework.
- `application/`    casos de uso (orquestan reglas de negocio usando los puertos).
- `infrastructure/` adaptadores: `repository.py` (SQLAlchemy), `router.py` (FastAPI),
                  `schemas.py` (Pydantic), `dependencies.py` (composición/DI).

Tabla(s) asociada(s) del .sql: ver `src/shared/models.py`.
Cuando crees el router, móntalo en `main.py` bajo el prefijo `/api/v1`.
