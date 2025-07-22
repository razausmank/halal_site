"""add restaurant table

Revision ID: efb1fe798eb4
Revises: 3feb07c440e2
Create Date: 2025-07-21 21:57:30.728021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'efb1fe798eb4'
down_revision: Union[str, Sequence[str], None] = '3feb07c440e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'restaurants',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('opening_hours', sa.String(), nullable=True),
        sa.Column('cuisine_type', sa.String(), nullable=True),
        sa.Column('price_range', sa.String(), nullable=True),
        sa.Column('halal_status', sa.String(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('scraped_json', sa.JSON(), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('restaurants')
