"""align funnel setup payload contract

Revision ID: e4b7c2a1f9d0
Revises: c1a4d9f8e2b7
Create Date: 2026-04-09 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e4b7c2a1f9d0"
down_revision: Union[str, None] = "c1a4d9f8e2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "funnels",
        sa.Column("style", sa.Text(), server_default="high_converting", nullable=False),
    )
    op.add_column(
        "funnels",
        sa.Column(
            "integrations",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )

    op.execute("ALTER TYPE funnel_status ADD VALUE IF NOT EXISTS 'published'")

    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type DROP DEFAULT")
    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type TYPE text USING funnel_type::text")
    op.execute(
        """
        UPDATE funnels
        SET funnel_type = CASE
            WHEN funnel_type = 'lead_magnet' THEN 'lead_generation'
            WHEN funnel_type = 'vsl' THEN 'call_funnel'
            WHEN funnel_type IN ('webinar', 'product_launch', 'book', 'application') THEN 'direct_sales'
            WHEN funnel_type IN ('lead_generation', 'call_funnel', 'direct_sales') THEN funnel_type
            ELSE 'direct_sales'
        END
        """
    )
    op.execute("DROP TYPE funnel_type")
    op.execute("CREATE TYPE funnel_type AS ENUM ('lead_generation', 'call_funnel', 'direct_sales')")
    op.execute(
        "ALTER TABLE funnels ALTER COLUMN funnel_type TYPE funnel_type USING funnel_type::funnel_type"
    )
    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type SET DEFAULT 'lead_generation'")


def downgrade() -> None:
    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type DROP DEFAULT")
    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type TYPE text USING funnel_type::text")
    op.execute(
        """
        UPDATE funnels
        SET funnel_type = CASE
            WHEN funnel_type = 'lead_generation' THEN 'lead_magnet'
            WHEN funnel_type = 'call_funnel' THEN 'vsl'
            WHEN funnel_type = 'direct_sales' THEN 'vsl'
            ELSE 'vsl'
        END
        """
    )
    op.execute("DROP TYPE funnel_type")
    op.execute(
        "CREATE TYPE funnel_type AS ENUM ('vsl', 'lead_magnet', 'webinar', 'product_launch', 'book', 'application')"
    )
    op.execute(
        "ALTER TABLE funnels ALTER COLUMN funnel_type TYPE funnel_type USING funnel_type::funnel_type"
    )
    op.execute("ALTER TABLE funnels ALTER COLUMN funnel_type SET DEFAULT 'vsl'")

    op.execute("ALTER TABLE funnels ALTER COLUMN status TYPE text USING status::text")
    op.execute("UPDATE funnels SET status = 'ready' WHERE status = 'published'")
    op.execute("DROP TYPE funnel_status")
    op.execute("CREATE TYPE funnel_status AS ENUM ('draft', 'generating', 'ready', 'error')")
    op.execute("ALTER TABLE funnels ALTER COLUMN status TYPE funnel_status USING status::funnel_status")
    op.execute("ALTER TABLE funnels ALTER COLUMN status SET DEFAULT 'draft'")

    op.drop_column("funnels", "integrations")
    op.drop_column("funnels", "style")
