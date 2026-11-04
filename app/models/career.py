from typing import Optional
from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedModel


class JobPosting(TimeStampedModel):
    __tablename__ = "job_postings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    team: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="Full-time / Remote")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="Remote (India)")
    emoji: Mapped[str] = mapped_column(String(20), nullable=False, default="📚")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    apply_email: Mapped[str] = mapped_column(
        String(255), nullable=False, default="support@cosmoindiaprakashan.in"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<JobPosting {self.title} ({self.location})>"


class JobApplication(TimeStampedModel):
    __tablename__ = "job_applications"

    job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    applicant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    applicant_email: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted")

    def __repr__(self) -> str:
        return f"<JobApplication {self.applicant_name} ({self.applicant_email})>"

