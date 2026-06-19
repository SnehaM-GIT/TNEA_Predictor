"""add category_locked to users

Revision ID: b3c9f2d7a4e1
Revises: 188d74606c70
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c9f2d7a4e1'
down_revision: Union[str, Sequence[str], None] = '188d74606c70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('category_locked', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'category_locked')
