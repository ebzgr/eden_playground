"""Experiment schedule, explanation, and status history.

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    exp_cols = {c["name"] for c in insp.get_columns("experiments")}

    if "starts_at" not in exp_cols:
        op.add_column(
            "experiments",
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "ends_at" not in exp_cols:
        op.add_column(
            "experiments",
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "explanation" not in exp_cols:
        op.add_column(
            "experiments",
            sa.Column("explanation", sa.Text(), nullable=True),
        )

    op.execute(
        """
        UPDATE experiments
        SET starts_at = COALESCE(starts_at, created_at, CURRENT_TIMESTAMP),
            ends_at = COALESCE(
                ends_at,
                datetime(COALESCE(created_at, CURRENT_TIMESTAMP), '+30 days')
            ),
            explanation = COALESCE(explanation, '')
        WHERE starts_at IS NULL OR ends_at IS NULL OR explanation IS NULL
        """
    )

    with op.batch_alter_table("experiments") as batch_op:
        batch_op.alter_column("starts_at", nullable=False)
        batch_op.alter_column("ends_at", nullable=False)
        batch_op.alter_column("explanation", nullable=False)

    if not insp.has_table("experiment_status_history"):
        op.create_table(
            "experiment_status_history",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("experiment_id", sa.String(128), nullable=False),
            sa.Column("action", sa.String(32), nullable=False),
            sa.Column("previous_state", sa.String(32), nullable=True),
            sa.Column("new_state", sa.String(32), nullable=True),
            sa.Column(
                "previous_ends_at", sa.DateTime(timezone=True), nullable=True
            ),
            sa.Column("new_ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_experiment_status_history_experiment_id",
            "experiment_status_history",
            ["experiment_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("experiment_status_history"):
        op.drop_index(
            "ix_experiment_status_history_experiment_id",
            table_name="experiment_status_history",
        )
        op.drop_table("experiment_status_history")
    exp_cols = {c["name"] for c in insp.get_columns("experiments")}
    if "explanation" in exp_cols:
        op.drop_column("experiments", "explanation")
    if "ends_at" in exp_cols:
        op.drop_column("experiments", "ends_at")
    if "starts_at" in exp_cols:
        op.drop_column("experiments", "starts_at")
