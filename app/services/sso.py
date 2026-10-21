from typing import Any, Dict
import httpx
from fastapi import HTTPException, status
from app.core.config import settings


async def verify_sso_code_with_main_platform(code: str) -> Dict[str, Any]:
    """
    Performs server-to-server verification of the one-time SSO code
    with the main VartaLang platform.
    """
    # 1. Dev/Mock fallback for local testing when main platform is offline
    if settings.DEBUG and code.startswith("mock_"):
        # e.g., mock_student_123 or mock_instructor_456
        role = "instructor" if "instructor" in code else "student"
        return {
            "vartalang_user_id": f"vl_{code}",
            "email": f"{code}@vartalang.in",
            "full_name": f"VartaLang {role.capitalize()}",
            "role": role,
            "avatar_url": None,
        }

    # 2. Production / Live server-to-server verification
    headers = {
        "Content-Type": "application/json",
        "X-SSO-Secret": settings.SSO_SHARED_SECRET,
    }
    payload = {"code": code}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.VARTALANG_MAIN_AUTH_URL,
                json=payload,
                headers=headers,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or previously redeemed SSO authorization code.",
            )

        data = response.json()
        user_info = data.get("user")
        if not user_info or not user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Malformed user payload received from VartaLang identity provider.",
            )

        return {
            "vartalang_user_id": str(user_info.get("id") or user_info.get("vartalang_user_id")),
            "email": user_info["email"],
            "full_name": user_info.get("full_name") or user_info.get("name") or "VartaLang User",
            "role": user_info.get("role", "student").lower(),
            "avatar_url": user_info.get("avatar_url") or user_info.get("avatar"),
        }

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach Main VartaLang identity server: {str(exc)}",
        )
