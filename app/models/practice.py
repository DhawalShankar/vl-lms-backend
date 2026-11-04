from typing import Optional
from sqlalchemy import Boolean, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedModel


class PracticeLab(TimeStampedModel):
    __tablename__ = "practice_labs"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="free")  # 'free' | 'premium'
    duration: Mapped[str] = mapped_column(String(50), nullable=False, default="10-15 min")
    exercises: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    gradient: Mapped[str] = mapped_column(String(100), nullable=False, default="from-blue-500 to-indigo-600")
    highlights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    eta: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<PracticeLab {self.slug} ({self.title})>"


class PracticeSession(TimeStampedModel):
    __tablename__ = "practice_sessions"

    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    lab_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="Hindi")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<PracticeSession Lab:{self.lab_id} Score:{self.score}>"

