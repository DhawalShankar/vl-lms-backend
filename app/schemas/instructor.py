from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InstructorProfileIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    title: str = Field("Language Educator & Linguistic Mentor", max_length=200)
    bio: str = Field("Passionate about making Indian regional languages accessible.", max_length=2000)
    languages: List[str] = ["Hindi", "English"]
    experienceYears: int = 5
    avatarUrl: Optional[str] = ""
    twitter: Optional[str] = ""
    linkedin: Optional[str] = ""
    youtube: Optional[str] = ""
    website: Optional[str] = ""
    upiId: Optional[str] = ""
    bankAccount: Optional[str] = ""


class InstructorProfileOut(BaseModel):
    name: str
    title: str
    bio: str
    languages: List[str] = []
    experienceYears: int = 5
    avatarUrl: Optional[str] = ""
    twitter: Optional[str] = ""
    linkedin: Optional[str] = ""
    youtube: Optional[str] = ""
    website: Optional[str] = ""
    upiId: Optional[str] = ""
    bankAccount: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

