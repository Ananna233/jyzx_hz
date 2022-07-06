"""empty message

Revision ID: 8131f2b5e33f
Revises: 3f765179d267
Create Date: 2021-04-21 09:58:33.306394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8131f2b5e33f'
down_revision = '3f765179d267'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('update_record_info',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('u_ID', sa.String(length=18), nullable=False),
    sa.Column('u_new_comment', sa.Text(), nullable=True),
    sa.Column('u_name', sa.String(length=10), nullable=True),
    sa.Column('u_update_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('update_record_info')
    # ### end Alembic commands ###