"""user login tracking and soft delete

Revision ID: ca2c90ba3e23
Revises: aca3f3a69b30
Create Date: 2026-11-06 11:08:26.234731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca2c90ba3e23'
down_revision: Union[str, Sequence[str], None] = 'aca3f3a69b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users", sa.Column("login_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])
 
    # Backfill: every user created through real SSO has logged in at least once.
    # Dev / mock accounts are excluded so they do not inflate the numbers.
    op.execute(
        """
        UPDATE users
        SET first_login_at = created_at,
            last_login_at = created_at,
            login_count = 1
        WHERE vartalang_user_id IS NOT NULL
          AND vartalang_user_id NOT LIKE 'dev%'
          AND vartalang_user_id NOT LIKE 'vl_mock%'
        """
    )
 
 
def downgrade() -> None:
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "login_count")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "first_login_at")
