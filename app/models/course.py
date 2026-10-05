from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid6
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.enrollment import Enrollment, LessonProgress
    from app.models.payment import Payment
    from app.models.group import Group


class Course(TimeStampedModel):
    __tablename__ = "courses"

    instructor_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    level: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Beginner"
    )  # e.g., 'A1 - Beginner', 'B1 - Intermediate'
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # 'draft' | 'published' | 'archived'

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="courses_taught")
    modules: Mapped[List["Module"]] = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.order_index",
    )
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="course"
    )
    course_group: Mapped[Optional["Group"]] = relationship(
        "Group", back_populates="course", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def is_free(self) -> bool:
        return self.price == Decimal("0.00")

    def __repr__(self) -> str:
        return f"<Course {self.title} ({self.status})>"


class Module(TimeStampedModel):
    __tablename__ = "modules"

    course_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )

    def __repr__(self) -> str:
        return f"<Module {self.title} (Order: {self.order_index})>"


class Lesson(TimeStampedModel):
    __tablename__ = "lessons"

    module_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # YouTube Unlisted Video ID (e.g., "dQw4w9WgXcQ")
    notes_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Google Drive Notes link
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    module: Mapped["Module"] = relationship("Module", back_populates="lessons")
    progress_records: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Lesson {self.title} (Order: {self.order_index})>"
