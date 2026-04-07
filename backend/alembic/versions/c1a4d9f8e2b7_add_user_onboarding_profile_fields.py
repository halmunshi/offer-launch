"""add user onboarding profile fields

Revision ID: c1a4d9f8e2b7
Revises: 9f3c2b7d4a11
Create Date: 2026-04-07 15:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1a4d9f8e2b7"
down_revision: Union[str, None] = "9f3c2b7d4a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("business_type", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("industry", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "industry")
    op.drop_column("users", "business_type")
