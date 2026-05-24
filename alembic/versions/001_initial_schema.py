"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id_hash", sa.String(64), nullable=False),
        sa.Column("consent_state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id_hash"),
    )
    op.create_index("ix_users_user_id_hash", "users", ["user_id_hash"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.String(128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "worlds",
        sa.Column("id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("default_scene_id", sa.String(128), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scenes",
        sa.Column("id", sa.String(128), nullable=False),
        sa.Column("world_id", sa.String(128), nullable=False),
        sa.Column("default_version_id", sa.String(128), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scene_versions",
        sa.Column("scene_id", sa.String(128), nullable=False),
        sa.Column("id", sa.String(128), nullable=False),
        sa.Column("patch_spec", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"]),
        sa.PrimaryKeyConstraint("scene_id", "id"),
    )

    op.create_table(
        "experiments",
        sa.Column("id", sa.String(128), nullable=False),
        sa.Column("target_scope", sa.String(32), nullable=False),
        sa.Column("assignment_scope", sa.String(32), nullable=False),
        sa.Column("target", sa.JSON(), nullable=False),
        sa.Column("arms", sa.JSON(), nullable=False),
        sa.Column("guardrails", sa.JSON(), nullable=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assignments",
        sa.Column("subject_type", sa.String(16), nullable=False),
        sa.Column("subject_id", sa.String(64), nullable=False),
        sa.Column("experiment_id", sa.String(128), nullable=False),
        sa.Column("arm_id", sa.String(128), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("subject_type", "subject_id", "experiment_id"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(128), nullable=True),
        sa.Column("scene_id", sa.String(128), nullable=True),
        sa.Column("scene_version_id", sa.String(128), nullable=True),
        sa.Column("experiment_arms", sa.JSON(), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("ts_client", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ts_server", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_ts_server", "events", ["ts_server"])
    op.create_index("ix_events_world_id", "events", ["world_id"])
    op.create_index("ix_events_scene_id", "events", ["scene_id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])

    op.create_table(
        "player_state",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(256), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "key"),
    )


def downgrade() -> None:
    op.drop_table("player_state")
    op.drop_table("events")
    op.drop_table("assignments")
    op.drop_table("experiments")
    op.drop_table("scene_versions")
    op.drop_table("scenes")
    op.drop_table("worlds")
    op.drop_table("consents")
    op.drop_table("sessions")
    op.drop_table("users")
