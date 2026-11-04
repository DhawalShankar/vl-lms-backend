"""make lesson_progress completed_at nullable

Revision ID: b394a589d393
Revises: 7b891e4a1234
Create Date: 2026-11-04 21:40:03.037188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b394a589d393'
down_revision: Union[str, Sequence[str], None] = '7b891e4a1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'lesson_progress',
        'completed_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        existing_server_default=sa.text('now()'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Note: this fails if any rows currently have completed_at = NULL.
    # Backfill first if you ever need to roll back:
    #   UPDATE lesson_progress SET completed_at = now() WHERE completed_at IS NULL;
    op.alter_column(
        'lesson_progress',
        'completed_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text('now()'),
    )