from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PracticeLabOut(BaseModel):
    id: str
    title: str
    description: str
    type: str = "free"  # "free" | "premium"
    duration: str = "10-15 min"
    exercises: int = 15
    gradient: str = "from-blue-500 to-indigo-600"
    highlights: List[str] = []
    eta: Optional[str] = "Q4 2026"

    model_config = ConfigDict(from_attributes=True)


class ProgressStats(BaseModel):
    totalSessions: int = 0
    completedLabs: int = 0
    mentorReviews: int = 0
    streakDays: int = 0
    todaysPractice: int = 0


class PracticeProgressResponse(BaseModel):
    progress: ProgressStats


class PracticeEvaluateRequest(BaseModel):
    lab_id: str
    language: str = "Hindi"
    audio_base64: Optional[str] = None
    transcript_input: Optional[str] = None
    exercise_index: Optional[int] = 1


class PracticeEvaluateResponse(BaseModel):
    accuracy_percentage: float
    score: float
    feedback: str
    phoneme_details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []

