from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

# Authentication & Single Sign-On
api_router.include_router(auth.router, prefix="/auth", tags=["Auth & SSO"])

# Routers to be added in upcoming slices:
# api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
# api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
# api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
# api_router.include_router(groups.router, prefix="/groups", tags=["Groups & Chat"])
# api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
