"""codes table

Revision ID: f8ccee4de99f
Revises: 80fa0d24b984
Create Date: 2018-06-03 14:33:46.550694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8ccee4de99f'
down_revision = '80fa0d24b984'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('code', sa.Column('path', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('code', 'path')
    # ### end Alembic commands ###
