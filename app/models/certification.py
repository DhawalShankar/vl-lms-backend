from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedModel


class Certification(TimeStampedModel):
    __tablename__ = "certifications"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(100), nullable=False, default="from-amber-500 to-orange-600")
    eta: Mapped[str] = mapped_column(String(50), nullable=False, default="Q1 2027")
    levels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Certification {self.slug} ({self.title})>"


class UserCertification(TimeStampedModel):
    __tablename__ = "user_certifications"

    certificate_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(150), nullable=False)
    certification_title: Mapped[str] = mapped_column(String(150), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="Hindi")
    proficiency_level: Mapped[str] = mapped_column(String(50), nullable=False, default="Beginner")
    issue_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verification_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="valid")

    def __repr__(self) -> str:
        return f"<UserCertification {self.certificate_id} ({self.user_name})>"

