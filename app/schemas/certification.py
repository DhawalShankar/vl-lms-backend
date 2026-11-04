from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CertificationOut(BaseModel):
    id: str
    title: str
    desc: str
    color: str = "from-amber-500 to-orange-600"
    eta: str = "Q1 2027"
    levels: List[str] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CertificationVerifyRequest(BaseModel):
    certificate_id: str


class CertificationVerifyResponse(BaseModel):
    valid: bool
    certificate_id: str
    recipient_name: Optional[str] = None
    certification_title: Optional[str] = None
    language: Optional[str] = None
    proficiency_level: Optional[str] = None
    issue_date: Optional[datetime] = None
    issuer: str = "VartaLang National Linguistic Council"

