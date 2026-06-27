"""Cifrado en reposo de usuarios.telefono.

El teléfono pasa a guardarse cifrado (Fernet). El token cifrado es mucho más
largo que el original, así que se amplía la columna de VARCHAR(20) a VARCHAR(255).

OJO: si ya hay teléfonos en claro en la BD, hay que cifrarlos (data migration)
antes de leerlos. En este proyecto aún no hay datos productivos.

Revision ID: 0004_encrypt_telefono
Revises: 0003_google_auth
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_encrypt_telefono"
down_revision: Union[str, None] = "0003_google_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("usuarios") as batch:
        batch.alter_column(
            "telefono",
            existing_type=sa.String(20),
            type_=sa.String(255),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("usuarios") as batch:
        batch.alter_column(
            "telefono",
            existing_type=sa.String(255),
            type_=sa.String(20),
            existing_nullable=True,
        )
