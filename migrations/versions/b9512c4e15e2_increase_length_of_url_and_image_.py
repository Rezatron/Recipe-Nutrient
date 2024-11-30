"""Increase length of url and image columns in recipe table

Revision ID: b9512c4e15e2
Revises: 32dcdb8b09e0
Create Date: 2024-11-30 15:28:41.995248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9512c4e15e2'
down_revision = '32dcdb8b09e0'
branch_labels = None
depends_on = None

def upgrade():
    # Increase length of url and image columns
    op.alter_column('recipe', 'url', type_=sa.String(500))
    op.alter_column('recipe', 'image', type_=sa.String(500))

def downgrade():
    # Revert length of url and image columns
    op.alter_column('recipe', 'url', type_=sa.String(300))
    op.alter_column('recipe', 'image', type_=sa.String(300))
