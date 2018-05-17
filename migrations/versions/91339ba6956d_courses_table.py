"""courses table

Revision ID: 91339ba6956d
Revises: af052175e691
Create Date: 2018-05-16 22:16:35.871828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91339ba6956d'
down_revision = 'af052175e691'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('course',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('course')
    # ### end Alembic commands ###
