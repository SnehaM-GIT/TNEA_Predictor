"""normalize email case and add case-insensitive unique index

Revision ID: f1a2b3c4d5e6
Revises: e9f7a2b4c8d1
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e9f7a2b4c8d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Normalize all existing email values to lowercase
    conn.execute(sa.text("UPDATE users SET email = LOWER(TRIM(email)) WHERE email IS NOT NULL"))

    # 2. Add functional unique index on LOWER(email) — guards against future regressions
    #    This will FAIL if step 1 above left case-variant duplicates; resolve those manually first.
    conn.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email))"
    ))


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_email_lower")
