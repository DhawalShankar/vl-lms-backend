"""course approval workflow

Revision ID: 43564d7f5e07
Revises: 9784511dc6a3
Create Date: 2026-11-06 15:01:55.379697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43564d7f5e07'
down_revision: Union[str, Sequence[str], None] = '9784511dc6a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
