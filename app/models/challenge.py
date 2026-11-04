from typing import Optional
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedModel


class Challenge(TimeStampedModel):
    __tablename__ = "challenges"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(50), nullable=False, default="daily_duel")
    color: Mapped[str] = mapped_column(String(100), nullable=False, default="from-red-500 to-orange-600")
    eta: Mapped[str] = mapped_column(String(50), nullable=False, default="Q4 2026")
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Challenge {self.slug} ({self.title})>"


class ChallengeLeaderboard(TimeStampedModel):
    __tablename__ = "challenge_leaderboard"

    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="Hindi")
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    def __repr__(self) -> str:
        return f"<ChallengeLeaderboard {self.user_name} XP:{self.xp}>"

