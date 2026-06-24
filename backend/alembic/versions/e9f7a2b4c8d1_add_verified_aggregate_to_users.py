"""add verified_aggregate to users

Revision ID: e9f7a2b4c8d1
Revises: b3c9f2d7a4e1
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f7a2b4c8d1'
down_revision: Union[str, Sequence[str], None] = 'b3c9f2d7a4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'verified_aggregate' not in columns:
        op.add_column('users', sa.Column('verified_aggregate', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'verified_aggregate')