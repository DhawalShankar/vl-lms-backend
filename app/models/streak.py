from datetime import date
from typing import List, Optional, TYPE_CHECKING
import uuid6
from sqlalchemy import Date, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User


class UserStreakRecord(TimeStampedModel):
    __tablename__ = "user_streaks"

    user_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_visit_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    total_days_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="streak_record")

    def __repr__(self) -> str:
        return f"<UserStreakRecord User:{self.user_id} Streak:{self.current_streak}>"

