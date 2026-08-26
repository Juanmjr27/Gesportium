"""añade datos_cuestionario y motivo_rechazo a borradores_ia, renombra tipo nutricion a plan_nutricional
 
Revision ID: 5fe144b91322
Revises: 2abd213f134d
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
 
# revision identifiers, used by Alembic.
revision = "5fe144b91322"
down_revision = "2abd213f134d"
branch_labels = None
depends_on = None
 
 
def upgrade() -> None:
    # datos_cuestionario: NOT NULL, pero la tabla puede tener filas ya
    # existentes -> se añade con server_default temporal y luego se
    # retira, para no romper filas previas ni dejar el default en el
    # esquema a largo plazo (la app siempre lo envía explícitamente).
    op.add_column(
        "borradores_ia",
        sa.Column(
            "datos_cuestionario",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.alter_column("borradores_ia", "datos_cuestionario", server_default=None)
 
    op.add_column(
        "borradores_ia",
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
    )
 
    op.execute(
        "UPDATE borradores_ia SET tipo = 'plan_nutricional' WHERE tipo = 'nutricion'"
    )
 
 
def downgrade() -> None:
    op.execute(
        "UPDATE borradores_ia SET tipo = 'nutricion' WHERE tipo = 'plan_nutricional'"
    )
    op.drop_column("borradores_ia", "motivo_rechazo")
    op.drop_column("borradores_ia", "datos_cuestionario")