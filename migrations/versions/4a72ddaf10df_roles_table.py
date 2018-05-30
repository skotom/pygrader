"""roles table

Revision ID: 4a72ddaf10df
Revises: 577c459b229c
Create Date: 2018-05-27 14:56:20.171699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4a72ddaf10df'
down_revision = '577c459b229c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles_users',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.add_column('role', sa.Column('description', sa.String(length=255), nullable=True))
    op.drop_constraint('user_ibfk_1', 'user', type_='foreignkey')
    op.drop_column('user', 'role_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('role_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('user_ibfk_1', 'user', 'role', ['role_id'], ['id'])
    op.drop_column('role', 'description')
    op.drop_table('roles_users')
    # ### end Alembic commands ###