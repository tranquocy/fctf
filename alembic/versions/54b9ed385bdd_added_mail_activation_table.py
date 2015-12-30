"""Added mail activation table

Revision ID: 54b9ed385bdd
Revises: 4809bb0fa09
Create Date: 2015-12-30 14:33:43.134586

"""

# revision identifiers, used by Alembic.
revision = '54b9ed385bdd'
down_revision = '4809bb0fa09'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_mail_activations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('token', sa.String(length=40), nullable=True),
    sa.Column('expire_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('users', 'email',
               existing_type=mysql.VARCHAR(length=45),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'email',
               existing_type=mysql.VARCHAR(length=45),
               nullable=True)
    op.drop_table('user_mail_activations')
    ### end Alembic commands ###
