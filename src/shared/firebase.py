"""Inicialización perezosa de Firebase Admin (para FCM).

Se inicializa una sola vez, a partir del JSON del service account que viene en
la variable de entorno FIREBASE_CREDENTIALS. `firebase_admin` se importa dentro
de la función para que la app NO dependa de la librería si el push está apagado.
"""
import json
from functools import lru_cache

from src.core.config import settings
from src.shared.errors import DomainError


class FirebaseError(DomainError):
    code = "firebase_error"
    status_code = 502


@lru_cache
def ensure_firebase() -> None:
    """Garantiza que la app de Firebase Admin esté inicializada (idempotente)."""
    if not settings.firebase_enabled:
        raise FirebaseError("FIREBASE_CREDENTIALS no está configurado.")
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as exc:  # pragma: no cover
        raise FirebaseError(
            "firebase-admin no está instalado en el entorno."
        ) from exc

    if not firebase_admin._apps:
        info = json.loads(settings.firebase_credentials)
        firebase_admin.initialize_app(credentials.Certificate(info))
