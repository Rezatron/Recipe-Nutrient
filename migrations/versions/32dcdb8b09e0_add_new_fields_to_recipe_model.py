"""Add new fields to Recipe model

Revision ID: 32dcdb8b09e0
Revises: c7e58f6ac88b
Create Date: 2024-11-25 13:26:36.506026

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32dcdb8b09e0'
down_revision = 'c7e58f6ac88b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ingredient_lines', sa.Text(), nullable=False))
        batch_op.add_column(sa.Column('micro_nutrients_per_serving', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('nutrient_units', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('comparison_to_rni', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.drop_column('comparison_to_rni')
        batch_op.drop_column('nutrient_units')
        batch_op.drop_column('micro_nutrients_per_serving')
        batch_op.drop_column('ingredient_lines')

    # ### end Alembic commands ###
