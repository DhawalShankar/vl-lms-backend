from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class UserStreakOut(BaseModel):
    currentStreak: int
    longestStreak: int
    lastVisitDate: str  # "YYYY-MM-DD"
    totalDaysActive: int
    history: List[str] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserStreakHeartbeatIn(BaseModel):
    localDate: Optional[str] = None  # Optional client local date "YYYY-MM-DD"

