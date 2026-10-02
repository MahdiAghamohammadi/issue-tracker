"""Add users and issue ownership.

Revision ID: 20261002_02
Revises: 20261002_01
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_02"
down_revision: str | None = "20261002_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.add_column("issues", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_issues_owner_id_users",
        "issues",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_issues_owner_id", "issues", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_issues_owner_id", table_name="issues")
    op.drop_constraint(
        "fk_issues_owner_id_users",
        "issues",
        type_="foreignkey",
    )
    op.drop_column("issues", "owner_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
