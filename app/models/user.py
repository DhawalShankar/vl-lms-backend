from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enrollment import Enrollment, LessonProgress
    from app.models.payment import Payment
    from app.models.group import Group, GroupMember, Message


class User(TimeStampedModel):
    __tablename__ = "users"

    # SSO Linkage with Main VartaLang Platform
    vartalang_user_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="student"
    )  # 'student' | 'instructor' | 'admin'
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    courses_taught: Mapped[List["Course"]] = relationship(
        "Course", back_populates="instructor", cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
    lesson_progress: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )
    created_groups: Mapped[List["Group"]] = relationship(
        "Group", back_populates="creator"
    )
    group_memberships: Mapped[List["GroupMember"]] = relationship(
        "GroupMember", back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
