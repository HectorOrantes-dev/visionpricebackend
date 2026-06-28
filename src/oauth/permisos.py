"""Matriz central de permisos por rol (RBAC).

Un único lugar para definir qué roles pueden hacer qué. Las rutas usan:

    from src.oauth.permisos import Permisos
    from src.oauth.roles import require_roles

    Depends(require_roles(*Permisos.GESTION_EQUIPOS))

Roles: maestro_obra · contratista · arquitecto · ingeniero_civil
"""


class Permisos:
    # Todos los usuarios autenticados.
    TODOS = ("maestro_obra", "contratista", "arquitecto", "ingeniero_civil")

    # Cotizar (grabar, transcribir, calcular m², ver productos, PDF): todos.
    COTIZAR = TODOS

    # Gestión e historial de proyectos múltiples (el maestro de obra no).
    GESTION_PROYECTOS = ("contratista", "arquitecto", "ingeniero_civil")

    # Crear equipos y administrar la plantilla: solo dirección técnica.
    GESTION_EQUIPOS = ("arquitecto", "ingeniero_civil")

    # Exclusivo del Ingeniero Civil:
    AUDITORIA_PRECIOS = ("ingeniero_civil",)   # detección de anomalías
    ADMIN_RBAC = ("ingeniero_civil",)          # configurar accesos/perfiles
