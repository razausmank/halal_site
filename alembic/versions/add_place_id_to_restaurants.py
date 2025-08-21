"""add place_id to restaurants table

Revision ID: add_place_id_restaurants
Revises: 0e6c70758f5b
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_place_id_restaurants'
down_revision: Union[str, Sequence[str], None] = '0e6c70758f5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Add place_id column to restaurants table
    op.add_column('restaurants', sa.Column('place_id', sa.String(), nullable=True))
    
    # Create unique index on place_id
    op.create_index(op.f('ix_restaurants_place_id'), 'restaurants', ['place_id'], unique=True)

def downgrade() -> None:
    """Downgrade schema."""
    # Remove the index first
    op.drop_index(op.f('ix_restaurants_place_id'), table_name='restaurants')
    
    # Remove the place_id column
    op.drop_column('restaurants', 'place_id') 