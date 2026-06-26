"""Esquema inicial — módulo de usuarios VisionPrice (11 tablas + seed roles).

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB en Postgres, JSON en SQLite (local).
JSONType = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False, unique=True),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("correo", sa.String(150), nullable=False, unique=True),
        sa.Column("contrasena_hash", sa.String(255), nullable=False),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "fecha_registro", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "activo", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )

    op.create_table(
        "proyectos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("latitud", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitud", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "estado", sa.String(30), nullable=False, server_default="activo"
        ),
        sa.Column(
            "fecha_creacion", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "proyecto_colaboradores",
        sa.Column(
            "proyecto_id",
            sa.Integer(),
            sa.ForeignKey("proyectos.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            primary_key=True,
        ),
        sa.Column("rol_en_proyecto", sa.String(50), nullable=True),
        sa.Column(
            "fecha_asignacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "grabaciones_audio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.Column(
            "proyecto_id", sa.Integer(), sa.ForeignKey("proyectos.id"), nullable=True
        ),
        sa.Column("ruta_local", sa.String(255), nullable=True),
        sa.Column("ruta_servidor", sa.String(255), nullable=True),
        sa.Column("duracion_segundos", sa.Integer(), nullable=True),
        sa.Column("hash_archivo", sa.String(64), nullable=True),
        sa.Column(
            "estado_sincronizacion",
            sa.String(20),
            nullable=False,
            server_default="pendiente",
        ),
        sa.Column("fecha_grabacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_sincronizacion", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "transcripciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "grabacion_id",
            sa.Integer(),
            sa.ForeignKey("grabaciones_audio.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("modelo_voice_to_text", sa.String(100), nullable=True),
        sa.Column("confianza", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "fecha_procesamiento",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "extracciones_llm",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "transcripcion_id",
            sa.Integer(),
            sa.ForeignKey("transcripciones.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("parametros_json", JSONType, nullable=False),
        sa.Column("version_modelo", sa.String(50), nullable=True),
        sa.Column(
            "fecha_extraccion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "presupuestos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "proyecto_id", sa.Integer(), sa.ForeignKey("proyectos.id"), nullable=False
        ),
        sa.Column(
            "extraccion_id",
            sa.Integer(),
            sa.ForeignKey("extracciones_llm.id"),
            nullable=True,
        ),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.Column("total_estimado", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "estado", sa.String(30), nullable=False, server_default="borrador"
        ),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "detalle_presupuesto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "presupuesto_id",
            sa.Integer(),
            sa.ForeignKey("presupuestos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("material_id", sa.Integer(), nullable=True),
        sa.Column("proveedor_id", sa.Integer(), nullable=True),
        sa.Column("descripcion_actividad", sa.String(255), nullable=False),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column("unidad_medida", sa.String(20), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=True),
    )

    op.create_table(
        "documentos_pdf",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "presupuesto_id",
            sa.Integer(),
            sa.ForeignKey("presupuestos.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("ruta_archivo", sa.String(255), nullable=False),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "bitacora_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True
        ),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("tabla_afectada", sa.String(50), nullable=True),
        sa.Column("registro_id", sa.Integer(), nullable=True),
        sa.Column("detalles", JSONType, nullable=True),
        sa.Column("fecha", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_origen", sa.String(45), nullable=True),
    )

    # Índices recomendados
    op.create_index(
        "idx_grabaciones_estado_sync",
        "grabaciones_audio",
        ["estado_sincronizacion"],
    )
    op.create_index("idx_presupuestos_proyecto", "presupuestos", ["proyecto_id"])
    op.create_index(
        "idx_detalle_presupuesto_id", "detalle_presupuesto", ["presupuesto_id"]
    )
    op.create_index(
        "idx_bitacora_usuario_fecha", "bitacora_auditoria", ["usuario_id", "fecha"]
    )

    # Seed mínimo de roles
    roles = sa.table("roles", sa.column("nombre", sa.String))
    op.bulk_insert(
        roles,
        [
            {"nombre": "maestro_obra"},
            {"nombre": "contratista"},
            {"nombre": "arquitecto"},
            {"nombre": "ingeniero_civil"},
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_bitacora_usuario_fecha", table_name="bitacora_auditoria")
    op.drop_index("idx_detalle_presupuesto_id", table_name="detalle_presupuesto")
    op.drop_index("idx_presupuestos_proyecto", table_name="presupuestos")
    op.drop_index("idx_grabaciones_estado_sync", table_name="grabaciones_audio")
    op.drop_table("bitacora_auditoria")
    op.drop_table("documentos_pdf")
    op.drop_table("detalle_presupuesto")
    op.drop_table("presupuestos")
    op.drop_table("extracciones_llm")
    op.drop_table("transcripciones")
    op.drop_table("grabaciones_audio")
    op.drop_table("proyecto_colaboradores")
    op.drop_table("proyectos")
    op.drop_table("usuarios")
    op.drop_table("roles")
