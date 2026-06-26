"""Soporte de login/register con Google.

- usuarios.contrasena_hash -> nullable (cuentas Google no tienen contraseña)
- + usuarios.proveedor_auth ('local' | 'google')
- + usuarios.google_sub (único, vínculo con la cuenta de Google)

Revision ID: 0003_google_auth
Revises: 0002_callbacks_2fa
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_google_auth"
down_revision: Union[str, None] = "0002_callbacks_2fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("usuarios") as batch:
        batch.alter_column(
            "contrasena_hash",
            existing_type=sa.String(255),
            nullable=True,
        )
        batch.add_column(
            sa.Column(
                "proveedor_auth",
                sa.String(20),
                nullable=False,
                server_default="local",
            )
        )
        batch.add_column(sa.Column("google_sub", sa.String(255), nullable=True))
        batch.create_unique_constraint("uq_usuarios_google_sub", ["google_sub"])


def downgrade() -> None:
    with op.batch_alter_table("usuarios") as batch:
        batch.drop_constraint("uq_usuarios_google_sub", type_="unique")
        batch.drop_column("google_sub")
        batch.drop_column("proveedor_auth")
        batch.alter_column(
            "contrasena_hash",
            existing_type=sa.String(255),
            nullable=False,
        )
