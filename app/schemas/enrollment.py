from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EnrollmentOut(BaseModel):
    id: UUID
    course_id: UUID
    course_title: str
    course_thumbnail_url: Optional[str] = None
    course_language: str
    course_level: str
    status: str  # 'active' | 'completed' | 'cancelled'
    progress_percentage: float
    total_lessons: int
    completed_lessons: int
    enrolled_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LessonProgressToggleResponse(BaseModel):
    lesson_id: UUID
    is_completed: bool
    completed_at: Optional[datetime] = None
    course_progress_percentage: float
    completed_lessons: int
    total_lessons: int
    is_course_completed: bool


class CourseProgressDetail(BaseModel):
    course_id: UUID
    total_lessons: int
    completed_lessons: int
    progress_percentage: float
    completed_lesson_ids: List[UUID] = []
    is_completed: bool
