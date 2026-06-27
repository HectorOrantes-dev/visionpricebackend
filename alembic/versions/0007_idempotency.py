"""Tabla de idempotencia de peticiones.

Revision ID: 0007_idempotency
Revises: 0006_dispositivos
Create Date: 2026-06-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_idempotency"
down_revision: Union[str, None] = "0006_dispositivos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clave", sa.String(255), nullable=False, unique=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("metodo", sa.String(10), nullable=False),
        sa.Column("ruta", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="procesando"
        ),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_idempotency_clave", "idempotency_keys", ["clave"], unique=True
    )


def downgrade() -> None:
    op.drop_index("idx_idempotency_clave", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
