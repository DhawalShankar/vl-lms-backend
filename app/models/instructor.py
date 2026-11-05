# app/models/instructor.py
from typing import List, Optional, TYPE_CHECKING
import uuid6
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User


class InstructorProfile(TimeStampedModel):
    __tablename__ = "instructor_profiles"

    user_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, default="Language Educator & Linguistic Mentor"
    )
    bio: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Passionate about making Indian regional languages accessible to learners across India and the global diaspora.",
    )
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # Text, not String(500): avatar URLs (e.g. Google photos) can exceed 500 characters
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    twitter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    youtube: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="instructor_profile")

    def __repr__(self) -> str:
        return f"<InstructorProfile {self.name} ({self.title})>"