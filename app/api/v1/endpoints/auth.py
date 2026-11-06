# app/api/v1/endpoints/auth.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import DevLoginRequest, SSOExchangeRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.sso import verify_sso_code_with_main_platform

router = APIRouter()


def _record_login(user: User) -> None:
    """SSO login monitoring: first/last login time and a running login count."""
    now = datetime.now(timezone.utc)
    if user.first_login_at is None:
        user.first_login_at = now
    user.last_login_at = now
    user.login_count = (user.login_count or 0) + 1


@router.post(
    "/sso/exchange",
    response_model=TokenResponse,
    summary="Exchange VartaLang SSO one-time code for LMS session token",
)
async def exchange_sso_code(
    payload: SSOExchangeRequest,
    db: Session = Depends(get_db),
):
    """
    Core SSO Endpoint:
    1. Receives short-lived authorization code from LMS Frontend.
    2. Verifies code server-to-server with Main VartaLang identity server.
    3. Provisions or updates local User account in Neon DB.
    4. Issues new LMS JWT access token.
    """
    # 1. Verify code server-to-server
    identity = await verify_sso_code_with_main_platform(payload.code)
    email = identity["email"].lower()

    # 2. Find or create user in our database
    user = (
        db.query(User)
        .filter(
            (User.email == email)
            | (User.vartalang_user_id == identity["vartalang_user_id"])
        )
        .first()
    )

    if not user:
        # First-time SSO login -> provision new user record
        user = User(
            vartalang_user_id=identity["vartalang_user_id"],
            email=email,
            full_name=identity["full_name"],
            role=identity["role"],
            avatar_url=identity.get("avatar_url"),
        )
        _record_login(user)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Deleted by an admin: never re-create or re-activate. The main VartaLang account is untouched.
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been removed.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled.",
            )

        # Existing user -> sync role from main VartaLang (source of truth for roles)
        user.vartalang_user_id = identity["vartalang_user_id"]
        user.role = identity["role"]

        # Instructors manage their own name and photo in the LMS profile. Do not overwrite
        # those with the main-site values on every login (course cards read users.full_name).
        if user.instructor_profile is None:
            user.full_name = identity["full_name"]
            if identity.get("avatar_url"):
                user.avatar_url = identity["avatar_url"]

        _record_login(user)
        db.commit()
        db.refresh(user)

    # 3. Mint our own independent LMS JWT token
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )


@router.post(
    "/dev-login",
    response_model=TokenResponse,
    summary="Development login helper (only when ENABLE_DEV_LOGIN=true)",
)
def dev_login(
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Developer helper endpoint to quickly simulate student, instructor,
    or admin logins without requiring the main VartaLang server.
    Disabled unless ENABLE_DEV_LOGIN=true is explicitly set (keep it false in production).
    Dev logins are NOT counted in the SSO login stats.
    """
    if not settings.ENABLE_DEV_LOGIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(
            email=payload.email,
            full_name=payload.full_name or "Dev Tester",
            role=payload.role,
            vartalang_user_id=f"dev_{payload.email.split('@')[0]}",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been removed.",
            )
        # Update role if requested differently during testing
        if payload.role and user.role != payload.role:
            user.role = payload.role
            db.commit()
            db.refresh(user)

    token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=token, token_type="bearer", user=user)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and permissions.
    Protected by LMS Bearer token.
    """
    return current_user