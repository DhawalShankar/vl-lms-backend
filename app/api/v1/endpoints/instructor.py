from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user, require_role
from app.core.database import get_db
from app.models.instructor import InstructorProfile
from app.models.user import User
from app.schemas.instructor import InstructorProfileIn, InstructorProfileOut

router = APIRouter()

DEFAULT_TITLE = "Language Educator & Linguistic Mentor"
DEFAULT_BIO = (
    "Passionate about making Indian regional languages accessible to learners "
    "across India and the global diaspora."
)


def _profile_out(profile: InstructorProfile, include_private: bool) -> InstructorProfileOut:
    """Payout details (UPI / bank) are only included for the profile owner."""
    return InstructorProfileOut(
        name=profile.name,
        title=profile.title,
        bio=profile.bio,
        languages=profile.languages or ["Hindi", "English"],
        experienceYears=profile.experience_years,
        avatarUrl=profile.avatar_url or "",
        twitter=profile.twitter or "",
        linkedin=profile.linkedin or "",
        youtube=profile.youtube or "",
        website=profile.website or "",
        upiId=(profile.upi_id or "") if include_private else "",
        bankAccount=(profile.bank_account or "") if include_private else "",
    )


@router.get(
    "/profile",
    response_model=InstructorProfileOut,
    summary="Get instructor profile",
)
def get_instructor_profile(
    user_id: Optional[str] = Query(None, description="Optional instructor user id"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    target_id: Optional[UUID] = None
    if user_id:
        try:
            target_id = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")
    elif current_user:
        target_id = current_user.id

    is_owner = bool(current_user and target_id and current_user.id == target_id)

    if target_id:
        profile = (
            db.query(InstructorProfile)
            .filter(InstructorProfile.user_id == target_id)
            .first()
        )
        if profile:
            return _profile_out(profile, include_private=is_owner)

    # No saved profile yet: neutral defaults only (no fake social links or payout details)
    default_name = current_user.full_name if (current_user and is_owner) else "Language Educator"
    default_avatar = (current_user.avatar_url if (current_user and is_owner) else "") or ""
    return InstructorProfileOut(
        name=default_name,
        title=DEFAULT_TITLE,
        bio=DEFAULT_BIO,
        languages=["Hindi", "English"],
        experienceYears=5,
        avatarUrl=default_avatar,
        twitter="",
        linkedin="",
        youtube="",
        website="",
        upiId="",
        bankAccount="",
    )


@router.post(
    "/profile",
    response_model=InstructorProfileOut,
    summary="Save / update public instructor profile",
)
def save_instructor_profile(
    payload: InstructorProfileIn,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(InstructorProfile)
        .filter(InstructorProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        profile = InstructorProfile(
            user_id=current_user.id,
            name=payload.name,
            title=payload.title,
            bio=payload.bio,
            languages=payload.languages,
            experience_years=payload.experienceYears,
            avatar_url=payload.avatarUrl or current_user.avatar_url,
            twitter=payload.twitter,
            linkedin=payload.linkedin,
            youtube=payload.youtube,
            website=payload.website,
            upi_id=payload.upiId,
            bank_account=payload.bankAccount,
        )
        db.add(profile)
    else:
        profile.name = payload.name
        profile.title = payload.title
        profile.bio = payload.bio
        profile.languages = payload.languages
        profile.experience_years = payload.experienceYears
        profile.avatar_url = payload.avatarUrl or profile.avatar_url
        profile.twitter = payload.twitter
        profile.linkedin = payload.linkedin
        profile.youtube = payload.youtube
        profile.website = payload.website
        profile.upi_id = payload.upiId
        profile.bank_account = payload.bankAccount

    # Keep user's full_name and avatar synced
    current_user.full_name = payload.name
    if payload.avatarUrl:
        current_user.avatar_url = payload.avatarUrl

    db.commit()
    db.refresh(profile)

    # The owner just saved this, so private payout fields are included
    return _profile_out(profile, include_private=True)