from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.challenge import Challenge, ChallengeLeaderboard
from app.schemas.challenge import ChallengeOut, LeaderboardEntryOut

router = APIRouter()

DEFAULT_CHALLENGES = [
    {
        "id": "daily-duels",
        "title": "Daily Duels",
        "desc": "Head-to-head vocabulary battles against other learners — one language, one winner.",
        "type": "daily_duel",
        "color": "from-red-500 to-orange-600",
        "eta": "Q4 2026",
        "xp_reward": 150,
    },
    {
        "id": "script-sprint",
        "title": "Script Sprint",
        "desc": "Race to transliterate a passage correctly before the timer runs out.",
        "type": "script_sprint",
        "color": "from-blue-500 to-cyan-500",
        "eta": "Q4 2026",
        "xp_reward": 120,
    },
    {
        "id": "flashcard-blitz",
        "title": "Flashcard Blitz",
        "desc": "Rapid-fire word-to-meaning matching under pressure — as fast as you can.",
        "type": "flashcard_blitz",
        "color": "from-amber-500 to-yellow-500",
        "eta": "Q1 2027",
        "xp_reward": 100,
    },
    {
        "id": "weekly-leaderboard",
        "title": "Weekly Leaderboard",
        "desc": "Earn XP throughout the week and compete for a spot at the top of your language group.",
        "type": "weekly_leaderboard",
        "color": "from-purple-500 to-pink-500",
        "eta": "Q1 2027",
        "xp_reward": 250,
    },
]

DEFAULT_LEADERBOARD = [
    {"rank": 1, "user_name": "Aarav Sharma", "avatar_url": None, "language": "Hindi", "xp": 3450},
    {"rank": 2, "user_name": "Priya Sundaram", "avatar_url": None, "language": "Tamil", "xp": 3120},
    {"rank": 3, "user_name": "Rahul Verma", "avatar_url": None, "language": "Telugu", "xp": 2980},
    {"rank": 4, "user_name": "Ananya Roy", "avatar_url": None, "language": "Bengali", "xp": 2740},
    {"rank": 5, "user_name": "Vikram Patel", "avatar_url": None, "language": "Gujarati", "xp": 2510},
]


@router.get(
    "",
    response_model=List[ChallengeOut],
    summary="List upcoming and active language competitions & duels",
)
def list_challenges(db: Session = Depends(get_db)):
    try:
        challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
        if challenges:
            return [
                ChallengeOut(
                    id=c.slug,
                    title=c.title,
                    desc=c.description,
                    type=c.challenge_type,
                    color=c.color,
                    eta=c.eta,
                    xp_reward=c.xp_reward,
                )
                for c in challenges
            ]
    except Exception:
        pass

    return [ChallengeOut(**c) for c in DEFAULT_CHALLENGES]


@router.get(
    "/leaderboard",
    response_model=List[LeaderboardEntryOut],
    summary="Get current weekly global/vernacular leaderboard",
)
def get_leaderboard(db: Session = Depends(get_db)):
    try:
        entries = (
            db.query(ChallengeLeaderboard)
            .order_by(ChallengeLeaderboard.rank.asc())
            .limit(20)
            .all()
        )
        if entries:
            return [
                LeaderboardEntryOut(
                    rank=e.rank,
                    user_name=e.user_name,
                    avatar_url=e.avatar_url,
                    language=e.language,
                    xp=e.xp,
                )
                for e in entries
            ]
    except Exception:
        pass

    return [LeaderboardEntryOut(**e) for e in DEFAULT_LEADERBOARD]

