"""Add url column to listings table

Revision ID: 2308d3e147f9
Revises: bedc9c8b7145
Create Date: 2025-12-25 21:22:22.090483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2308d3e147f9'
down_revision: Union[str, Sequence[str], None] = 'bedc9c8b7145'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add url column to listings table
    op.add_column('listings', sa.Column('url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove url column from listings table
    op.drop_column('listings', 'url')
