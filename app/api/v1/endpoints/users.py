from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_optional_current_user
from app.core.database import get_db
from app.models.streak import UserStreakRecord
from app.models.user import User
from app.schemas.streak import UserStreakHeartbeatIn, UserStreakOut

router = APIRouter()


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _calc_day_diff(d1: date, d2: date) -> int:
    return (d2 - d1).days


@router.post(
    "/streak/heartbeat",
    response_model=UserStreakOut,
    summary="Record daily learner activity heartbeat & sync streak",
)
def record_streak_heartbeat(
    payload: Optional[UserStreakHeartbeatIn] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Records daily learner presence, updates streak count across devices,
    and returns hydrated UserStreak metadata for browser persistence.
    """
    today_str = payload.localDate if (payload and payload.localDate) else _format_date(date.today())
    today_date = datetime.strptime(today_str, "%Y-%m-%d").date() if today_str else date.today()

    if not current_user:
        # Fallback guest streak
        return UserStreakOut(
            currentStreak=1,
            longestStreak=1,
            lastVisitDate=today_str,
            totalDaysActive=1,
            history=[today_str],
        )

    streak = (
        db.query(UserStreakRecord)
        .filter(UserStreakRecord.user_id == current_user.id)
        .first()
    )

    if not streak:
        streak = UserStreakRecord(
            user_id=current_user.id,
            current_streak=1,
            longest_streak=1,
            last_visit_date=today_date,
            total_days_active=1,
            history=[today_str],
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)
    else:
        diff = _calc_day_diff(streak.last_visit_date, today_date)
        history_list = list(streak.history or [])

        if diff == 0:
            # Already active today
            if today_str not in history_list:
                history_list.append(today_str)
                streak.history = history_list[-30:]
                db.commit()
        elif diff == 1:
            # Visited yesterday: streak increments
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            streak.last_visit_date = today_date
            streak.total_days_active += 1
            if today_str not in history_list:
                history_list.append(today_str)
            streak.history = history_list[-30:]
            db.commit()
        elif diff > 1:
            # Missed a day or more: streak resets to 1
            streak.current_streak = 1
            streak.last_visit_date = today_date
            streak.total_days_active += 1
            if today_str not in history_list:
                history_list.append(today_str)
            streak.history = history_list[-30:]
            db.commit()

        db.refresh(streak)

    return UserStreakOut(
        currentStreak=streak.current_streak,
        longestStreak=streak.longest_streak,
        lastVisitDate=_format_date(streak.last_visit_date),
        totalDaysActive=streak.total_days_active,
        history=streak.history or [today_str],
    )


@router.get(
    "/streak",
    response_model=UserStreakOut,
    summary="Get current user's streak status",
)
def get_user_streak(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    today_str = _format_date(date.today())
    if not current_user:
        return UserStreakOut(
            currentStreak=1,
            longestStreak=1,
            lastVisitDate=today_str,
            totalDaysActive=1,
            history=[today_str],
        )

    streak = (
        db.query(UserStreakRecord)
        .filter(UserStreakRecord.user_id == current_user.id)
        .first()
    )

    if not streak:
        return UserStreakOut(
            currentStreak=1,
            longestStreak=1,
            lastVisitDate=today_str,
            totalDaysActive=1,
            history=[today_str],
        )

    return UserStreakOut(
        currentStreak=streak.current_streak,
        longestStreak=streak.longest_streak,
        lastVisitDate=_format_date(streak.last_visit_date),
        totalDaysActive=streak.total_days_active,
        history=streak.history or [today_str],
    )

