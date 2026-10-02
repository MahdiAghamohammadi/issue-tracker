"""Create issues table.

Revision ID: 20261002_01
Revises:
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

issue_priority = sa.Enum("low", "medium", "high", name="issue_priority")
issue_status = sa.Enum("open", "in_progress", "closed", name="issue_status")


def upgrade() -> None:
    op.create_table(
        "issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", issue_priority, nullable=False),
        sa.Column("status", issue_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_issues_created_at", "issues", ["created_at"])
    op.create_index("ix_issues_priority", "issues", ["priority"])
    op.create_index("ix_issues_status", "issues", ["status"])
    op.create_index("ix_issues_title", "issues", ["title"])


def downgrade() -> None:
    op.drop_index("ix_issues_title", table_name="issues")
    op.drop_index("ix_issues_status", table_name="issues")
    op.drop_index("ix_issues_priority", table_name="issues")
    op.drop_index("ix_issues_created_at", table_name="issues")
    op.drop_table("issues")
    issue_status.drop(op.get_bind(), checkfirst=True)
    issue_priority.drop(op.get_bind(), checkfirst=True)
