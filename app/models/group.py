from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid6
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course


class Group(TimeStampedModel):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    group_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="public"
    )  # 'public' | 'course'
    language: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # e.g., 'German', 'Spanish'
    course_id: Mapped[Optional[uuid6.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
    )
    created_by: Mapped[Optional[uuid6.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    course: Mapped[Optional["Course"]] = relationship(
        "Course", back_populates="course_group"
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User", back_populates="created_groups"
    )
    members: Mapped[List["GroupMember"]] = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Group {self.name} ({self.group_type})>"


class GroupMember(TimeStampedModel):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_member"),
    )

    group_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="member"
    )  # 'member' | 'moderator' | 'admin'
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")

    def __repr__(self) -> str:
        return f"<GroupMember User:{self.user_id} Group:{self.group_id} Role:{self.role}>"


class Message(Base):
    """
    Chat messages within a group.
    Notice: Since id is UUIDv7, it embeds the timestamp directly.
    """
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_group_id", "group_id", "id"),
    )

    id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        index=True,
    )
    group_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.id} Sender:{self.sender_id} Group:{self.group_id}>"
