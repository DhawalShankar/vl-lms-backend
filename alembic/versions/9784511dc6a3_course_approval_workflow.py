"""course approval workflow

Revision ID: 9784511dc6a3
Revises: ca2c90ba3e23
Create Date: 2026-11-06 11:12:32.875813

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql




# revision identifiers, used by Alembic.
revision: str = '9784511dc6a3'
down_revision: Union[str, Sequence[str], None] = 'ca2c90ba3e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column("courses", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("courses", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("courses", sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("courses", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("courses", sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "courses",
        sa.Column("managed_by_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.execute("UPDATE courses SET created_by = instructor_id")

    # Platform is not live yet: existing courses are test data. Put everything back to draft
    # so every course goes through approval. Delete this line to keep current courses live.
    op.execute("UPDATE courses SET status = 'draft' WHERE status = 'published'")


def downgrade() -> None:
    op.drop_column("courses", "managed_by_admin")
    op.drop_column("courses", "published_by")
    op.drop_column("courses", "created_by")
    op.drop_column("courses", "rejection_reason")
    op.drop_column("courses", "reviewed_by")
    op.drop_column("courses", "reviewed_at")
    op.drop_column("courses", "submitted_at")