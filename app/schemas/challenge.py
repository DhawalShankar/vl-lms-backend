from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ChallengeOut(BaseModel):
    id: str
    title: str
    desc: str
    type: str = "daily_duel"
    color: str = "from-red-500 to-orange-600"
    eta: str = "Q4 2026"
    xp_reward: int = 100

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_name: str
    avatar_url: Optional[str] = None
    language: str
    xp: int

    model_config = ConfigDict(from_attributes=True)

