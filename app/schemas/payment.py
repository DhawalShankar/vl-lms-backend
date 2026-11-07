from uuid import UUID

from pydantic import BaseModel, Field


class PaymentOrderCreate(BaseModel):
    course_id: UUID


class PaymentOrderOut(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=1, max_length=100)
    razorpay_payment_id: str = Field(..., min_length=1, max_length=100)
    razorpay_signature: str = Field(..., min_length=1, max_length=255)


class PaymentVerifyOut(BaseModel):
    success: bool
    order_id: str
    payment_id: str
