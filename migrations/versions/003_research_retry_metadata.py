"""Add durable research worker retry metadata.

Revision ID: 003_research_retry_metadata
Revises: 002_plan_entitlements
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_research_retry_metadata"
down_revision: Union[str, None] = "002_plan_entitlements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("research_tasks", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("research_tasks", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("research_tasks", "attempts", server_default=None)


def downgrade() -> None:
    op.drop_column("research_tasks", "started_at")
    op.drop_column("research_tasks", "attempts")
