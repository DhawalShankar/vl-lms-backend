from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    articles,
    auth,
    careers,
    certifications,
    challenges,
    courses,
    enrollments,
    instructor,
    practice,
    users,
)

api_router = APIRouter()

# Authentication & Single Sign-On
api_router.include_router(auth.router, prefix="/auth", tags=["Auth & SSO"])

# User Profiles & Daily Streaks
api_router.include_router(users.router, prefix="/users", tags=["Users & Streaks"])

# Instructor Studio & Public Profiles
api_router.include_router(instructor.router, prefix="/instructor", tags=["Instructor Studio"])

# Course Catalog, Hierarchy & Curriculum Builder
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])

# Student Enrollments & Lesson Progress Engine
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments & Progress"])

# Practice Labs & Speech Evaluation
api_router.include_router(practice.router, prefix="/practice", tags=["Practice Labs"])

# Challenges & Competitions
api_router.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])

# Official Certifications & Verification
api_router.include_router(certifications.router, prefix="/certifications", tags=["Certifications"])

# Blog, Articles & Pedagogical Insights
api_router.include_router(articles.router, prefix="/articles", tags=["Articles & Blog"])

# Career Openings & Job Applications
api_router.include_router(careers.router, prefix="/careers", tags=["Careers"])

# Platform Administration & Analytics
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Platform Analytics"])
