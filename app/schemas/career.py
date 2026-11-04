from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class JobPostingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    team: str = Field(..., max_length=100)
    type: str = "Full-time / Remote"
    location: str = "Remote (India)"
    emoji: str = "📚"
    description: Optional[str] = None
    requirements: List[str] = []
    apply_email: str = "support@cosmoindiaprakashan.in"


class JobPostingCreate(JobPostingBase):
    pass


class JobPostingOut(JobPostingBase):
    id: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class JobApplyRequest(BaseModel):
    job_id: Optional[str] = None
    applicant_name: str = Field(..., min_length=2, max_length=150)
    applicant_email: EmailStr
    resume_url: Optional[str] = None
    cover_note: Optional[str] = None

