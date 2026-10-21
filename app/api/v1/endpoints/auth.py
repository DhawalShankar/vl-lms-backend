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

    # 2. Find or create user in our database
    user = (
        db.query(User)
        .filter(
            (User.email == identity["email"])
            | (User.vartalang_user_id == identity["vartalang_user_id"])
        )
        .first()
    )

    if not user:
        # First-time SSO login -> Provision new student/instructor record
        user = User(
            vartalang_user_id=identity["vartalang_user_id"],
            email=identity["email"],
            full_name=identity["full_name"],
            role=identity["role"],
            avatar_url=identity.get("avatar_url"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Existing user -> Synchronize latest profile info
        user.vartalang_user_id = identity["vartalang_user_id"]
        user.full_name = identity["full_name"]
        user.role = identity["role"]
        if identity.get("avatar_url"):
            user.avatar_url = identity["avatar_url"]
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
    summary="Development login helper (Active in Development/Debug mode)",
)
def dev_login(
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Developer helper endpoint to quickly simulate student, instructor,
    or admin logins without requiring the main VartaLang server.
    """
    if not settings.DEBUG and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled in production environment.",
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
