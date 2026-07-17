"""Modelos SQLAlchemy — reflejan el esquema del .sql (PostgreSQL 16).

Estos son los adaptadores de persistencia compartidos por todas las features.
Las columnas y relaciones siguen 1:1 el bosquejo SQL del módulo de usuarios.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.core.database import Base
from src.shared.encrypted_types import EncryptedString

# JSONB en Postgres; JSON genérico en SQLite (local).
JSONType = JSONB().with_variant(JSON(), "sqlite")


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    # Nullable: los usuarios que entran con Google no tienen contraseña local.
    contrasena_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Dato sensible: cifrado en reposo (Fernet) vía EncryptedString. La columna
    # debe ser amplia porque el token cifrado es mucho más largo que el original.
    telefono: Mapped[str | None] = mapped_column(EncryptedString(255), nullable=True)
    # Origen de la cuenta y vínculo con Google (Sign-In).
    proveedor_auth: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="local", default="local"
    )  # local | google
    google_sub: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    rol_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    # Entitlement cacheado desde el microservicio de Pagos (vía webhook).
    # La fuente de verdad de la facturación sigue siendo el micro de Pagos.
    plan_activo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")


class Proyecto(Base):
    __tablename__ = "proyectos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="activo", default="activo"
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class ProyectoColaborador(Base):
    __tablename__ = "proyecto_colaboradores"

    proyecto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("proyectos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), primary_key=True
    )
    rol_en_proyecto: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class GrabacionAudio(Base):
    __tablename__ = "grabaciones_audio"
    __table_args__ = (
        Index(
            "uq_grabaciones_usuario_local",
            "usuario_id",
            "local_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    # Idempotencia de la cola offline: UUID que genera la app por grabación.
    local_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proyecto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=True
    )
    ruta_local: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ruta_servidor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Key/identificador del audio en el object storage del microservicio de ML.
    object_storage_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    duracion_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hash_archivo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estado_sincronizacion: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pendiente", default="pendiente"
    )
    fecha_grabacion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_sincronizacion: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Transcripcion(Base):
    __tablename__ = "transcripciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grabacion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grabaciones_audio.id"), unique=True, nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    modelo_voice_to_text: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    confianza: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    fecha_procesamiento: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class ExtraccionLLM(Base):
    __tablename__ = "extracciones_llm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcripcion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripciones.id"), unique=True, nullable=False
    )
    parametros_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    version_modelo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_extraccion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=False
    )
    extraccion_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracciones_llm.id"), nullable=True
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    total_estimado: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="borrador", default="borrador"
    )
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class DetallePresupuesto(Base):
    __tablename__ = "detalle_presupuesto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    presupuesto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("presupuestos.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Referencias LÓGICAS al microservicio de Proveedores (sin FK física).
    material_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proveedor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proveedor_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proveedor_distancia: Mapped[float | None] = mapped_column(Numeric(9, 2), nullable=True)
    descripcion_actividad: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unidad_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    precio_unitario: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    subtotal: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)


class RecomendacionUso(Base):
    """Cada llamada a POST /recomendaciones/kit, y si terminó usándose de
    verdad en una cotización (POST /cotizaciones/kit con recomendacion_id).
    El contador de "recomendaciones usadas" sale de contar `cotizacion_id IS
    NOT NULL` acá — no es un número en memoria, es auditable.
    """

    __tablename__ = "recomendaciones_uso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    proyecto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=True
    )
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_kit_recomendado: Mapped[str] = mapped_column(String(30), nullable=False)
    complementos_recomendados: Mapped[dict] = mapped_column(JSONType, nullable=False)
    metodo_crucetas_recomendado: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    fecha_solicitud: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    # Se completan solo si la recomendación se concretó en una cotización.
    cotizacion_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("presupuestos.id"), nullable=True
    )
    fecha_uso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DocumentoPDF(Base):
    __tablename__ = "documentos_pdf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    presupuesto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("presupuestos.id"), unique=True, nullable=False
    )
    ruta_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Desafio2FA(Base):
    """Registro de los desafíos de doble factor en el flujo de login.

    El CÓDIGO en sí lo guarda y valida el microservicio 2FA; esta tabla sólo
    lleva el estado del desafío (auditoría, intentos, IP, rate-limiting).
    """

    __tablename__ = "desafios_2fa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=True
    )
    correo: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    proposito: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="login", default="login"
    )  # login | registro
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pendiente", default="pendiente"
    )  # pendiente | verificado | bloqueado | expirado
    intentos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    ip_origen: Mapped[str | None] = mapped_column(String(45), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    fecha_verificacion: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Equipo(Base):
    """Equipo/plantilla de un arquitecto o ingeniero civil (propietario)."""

    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    propietario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class EquipoMiembro(Base):
    """Personas en la plantilla de un equipo (maestros, contratistas…)."""

    __tablename__ = "equipo_miembros"

    equipo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("equipos.id", ondelete="CASCADE"), primary_key=True
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), primary_key=True
    )
    rol_en_equipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Notificacion(Base):
    """Notificación in-app del usuario.

    IMPORTANTE: NO almacena datos sensibles (correo/teléfono). Solo referencia
    `usuario_id` + contenido no sensible. El destinatario real se resuelve en
    memoria al enviar y se descarta (no se persiste aquí).
    """

    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    cuerpo: Mapped[str] = mapped_column(String(500), nullable=False)
    canal: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="in_app", default="in_app"
    )  # in_app | email | push
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pendiente", default="pendiente"
    )  # pendiente | enviada | fallida
    referencia_tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    referencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leida: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class IdempotencyKey(Base):
    """Idempotencia de peticiones mutantes (evita doble procesamiento).

    Guarda la respuesta de la primera petición con una llave dada; si llega otra
    con la misma llave, se devuelve la respuesta guardada sin reprocesar.
    """

    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metodo: Mapped[str] = mapped_column(String(10), nullable=False)
    ruta: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="procesando", default="procesando"
    )  # procesando | completado
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)  # base64
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Dispositivo(Base):
    """Device token de FCM para enviar push a la app móvil del usuario.

    El `token` es un identificador opaco de dispositivo (no PII). No se expone
    en respuestas de la API y se desactiva si FCM lo reporta como inválido.
    """

    __tablename__ = "dispositivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    plataforma: Mapped[str] = mapped_column(String(20), nullable=False)  # android|ios|web
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class BitacoraAuditoria(Base):
    __tablename__ = "bitacora_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=True
    )
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    tabla_afectada: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registro_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalles: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    ip_origen: Mapped[str | None] = mapped_column(String(45), nullable=True)
