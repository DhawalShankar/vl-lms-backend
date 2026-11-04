from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_optional_current_user, require_role
from app.core.database import get_db
from app.models.instructor import InstructorProfile
from app.models.user import User
from app.schemas.instructor import InstructorProfileIn, InstructorProfileOut

router = APIRouter()


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
    target_user_id = user_id or (str(current_user.id) if current_user else None)

    if target_user_id:
        try:
            profile = (
                db.query(InstructorProfile)
                .filter(InstructorProfile.user_id == target_user_id)
                .first()
            )
            if profile:
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
                    upiId=profile.upi_id or "",
                    bankAccount=profile.bank_account or "",
                )
        except Exception:
            pass

    # Default profile response if no database record exists yet
    default_name = current_user.full_name if current_user else "Language Educator"
    default_avatar = current_user.avatar_url if current_user else ""
    return InstructorProfileOut(
        name=default_name,
        title="Language Educator & Linguistic Mentor",
        bio="Passionate about making Indian regional languages accessible to learners across India and the global diaspora.",
        languages=["Hindi", "English"],
        experienceYears=5,
        avatarUrl=default_avatar or "",
        twitter="https://x.com/vartalang",
        linkedin="https://linkedin.com/company/vartalang",
        youtube="https://youtube.com/@vartalang",
        website="https://vartalang.in",
        upiId="educator@upi",
        bankAccount="HDFC0001234 •••• 5678",
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
        upiId=profile.upi_id or "",
        bankAccount=profile.bank_account or "",
    )

