"""Add human-readable experiment name.

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("experiments")}
    if "name" not in cols:
        op.add_column(
            "experiments",
            sa.Column("name", sa.String(256), nullable=True),
        )
    op.execute(
        """
        UPDATE experiments
        SET name = COALESCE(NULLIF(name, ''), id)
        WHERE name IS NULL OR name = ''
        """
    )
    with op.batch_alter_table("experiments") as batch_op:
        batch_op.alter_column("name", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("experiments")}
    if "name" in cols:
        op.drop_column("experiments", "name")
