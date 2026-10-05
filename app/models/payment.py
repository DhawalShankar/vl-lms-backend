from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid6
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course


class Payment(TimeStampedModel):
    __tablename__ = "payments"

    user_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid6.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    razorpay_order_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    razorpay_signature: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="created"
    )  # 'created' | 'paid' | 'failed'

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    course: Mapped["Course"] = relationship("Course", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.razorpay_order_id} Amount:{self.amount} Status:{self.status}>"
