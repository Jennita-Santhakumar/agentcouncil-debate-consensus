"""initial debates and debate_rounds tables

Revision ID: 0001
Revises:
Create Date: 2026-09-22

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "debates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("num_rounds", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("pro_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("con_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("winner", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "debate_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "debate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("debates.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("pro_argument", sa.Text(), nullable=False),
        sa.Column("pro_score_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("con_argument", sa.Text(), nullable=False),
        sa.Column("con_score_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_debate_rounds_debate_id", "debate_rounds", ["debate_id"])


def downgrade() -> None:
    op.drop_index("ix_debate_rounds_debate_id", table_name="debate_rounds")
    op.drop_table("debate_rounds")
    op.drop_table("debates")
