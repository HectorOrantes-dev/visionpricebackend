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

    # Cotizar (crear cotización/kit/borrador, generar PDF): todos MENOS
    # contratista. El contratista administra su equipo de maestros de obra
    # (ver /proyectos/{id}/invitaciones) pero no genera cotizaciones él mismo.
    COTIZAR = ("maestro_obra", "arquitecto", "ingeniero_civil")

    # Gestión e historial de proyectos: todos los roles gestionan LOS SUYOS
    # (cada operación de /proyectos filtra por dueño = user.id). El maestro de
    # obra los crea desde la app móvil antes de grabar, así que también entra.
    GESTION_PROYECTOS = TODOS

    # Crear equipos y administrar la plantilla: solo dirección técnica.
    GESTION_EQUIPOS = ("arquitecto", "ingeniero_civil")

    # Exclusivo del Ingeniero Civil:
    AUDITORIA_PRECIOS = ("ingeniero_civil",)   # detección de anomalías
    ADMIN_RBAC = ("ingeniero_civil",)          # configurar accesos/perfiles
    ENTRENAR_MODELOS = ("ingeniero_civil",)    # reentrenar ML de recomendaciones

    # Pedir una recomendación de kit: todos (mismo criterio que COTIZAR).
    RECOMENDACIONES = TODOS
