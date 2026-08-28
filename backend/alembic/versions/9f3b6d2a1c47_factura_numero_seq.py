"""factura_numero_seq

Revision ID: 9f3b6d2a1c47
Revises: 5fe144b91322
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9f3b6d2a1c47'
down_revision: Union[str, Sequence[str], None] = '5fe144b91322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SEQUENCE de Postgres: nextval() es atómico y no transaccional (no se
    # ve afectado por rollback), así que dos transacciones concurrentes
    # nunca pueden obtener el mismo valor — a diferencia de contar filas de
    # `facturas` dentro de la propia transacción (specs/008 T5, hallazgo
    # confirmado en specs/018).
    op.execute("CREATE SEQUENCE factura_numero_seq START WITH 1 INCREMENT BY 1")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SEQUENCE factura_numero_seq")
