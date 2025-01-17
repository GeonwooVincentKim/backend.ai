"""Enlarge kernels.lang column length

Revision ID: 10e39a34eed5
Revises: d582942886ad
Create Date: 2018-10-29 13:52:10.583443

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '10e39a34eed5'
down_revision = 'd582942886ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kernels', 'lang',
                    existing_type=sa.String(length=64),
                    type_=sa.String(length=512))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('kernels', 'lang',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=64))
    # ### end Alembic commands ###
