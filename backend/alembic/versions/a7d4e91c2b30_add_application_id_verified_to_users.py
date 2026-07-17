"""add application_id_verified to users

Revision ID: a7d4e91c2b30
Revises: f1a2b3c4d5e6
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7d4e91c2b30'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'application_id_verified' not in columns:
        op.add_column(
            'users',
            sa.Column('application_id_verified', sa.Boolean(),
                      nullable=False, server_default=sa.false())
        )
        # Backfill: /predict/verify-rank (which matches against the official rank
        # list) has been the only writer of application_id up to this revision, so
        # every existing non-null value is a verified one. Without this, previously
        # verified users would come back as unverified and become overwritable
        # through /auth/update-profile.
        op.execute(
            "UPDATE users SET application_id_verified = TRUE "
            "WHERE application_id IS NOT NULL AND application_id <> ''"
        )


def downgrade() -> None:
    op.drop_column('users', 'application_id_verified')
