"""drop funnel_steps table

Revision ID: 9f3c2b7d4a11
Revises: 08a150a30733
Create Date: 2026-03-30 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f3c2b7d4a11"
down_revision: Union[str, None] = "08a150a30733"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_funnel_steps_type_unique")
    op.execute("DROP INDEX IF EXISTS idx_funnel_steps_order")
    op.execute("DROP INDEX IF EXISTS idx_funnel_steps_funnel_id")
    op.execute("DROP TABLE IF EXISTS funnel_steps")
    op.execute("DROP TYPE IF EXISTS step_status")
    op.execute("DROP TYPE IF EXISTS step_type")


def downgrade() -> None:
    op.execute(
        """
        CREATE TYPE step_type AS ENUM (
            'presell', 'optin', 'waiting_list', 'launch_coming', 'quiz',
            'vsl', 'sales', 'webinar_register', 'webinar_replay',
            'order', 'order_bump', 'application', 'book_call',
            'upsell', 'downsell', 'thankyou', 'members_area',
            'bridge', 'offer', 'case_study', 'demo', 'custom'
        )
        """
    )
    op.execute("CREATE TYPE step_status AS ENUM ('pending', 'generating', 'ready', 'error')")

    op.create_table(
        "funnel_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("funnel_id", sa.UUID(), nullable=False),
        sa.Column(
            "step_order",
            sa.Integer(),
            nullable=False,
            comment="1-based. Determines page sequence in the funnel.",
        ),
        sa.Column(
            "step_type",
            postgresql.ENUM(name="step_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "custom_step_name",
            sa.Text(),
            nullable=True,
            comment="v2 - only populated when step_type = custom. User-defined label.",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="step_status", create_type=False),
            server_default="pending",
            nullable=False,
            comment="Updated independently per step as assembler generates each page component.",
        ),
        sa.Column(
            "slug",
            sa.Text(),
            nullable=False,
            comment="URL-safe route slug. e.g. vsl-page -> /vsl-page in React Router.",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["funnel_id"], ["funnels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_funnel_steps_funnel_id", "funnel_steps", ["funnel_id"], unique=False)
    op.create_index("idx_funnel_steps_order", "funnel_steps", ["funnel_id", "step_order"], unique=False)
    op.create_index(
        "idx_funnel_steps_type_unique",
        "funnel_steps",
        ["funnel_id", "step_type"],
        unique=True,
    )
