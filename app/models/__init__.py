"""SQLAlchemy Database Models for VartaLang LMS."""

from app.core.database import Base
from app.models.base import TimeStampedModel
from app.models.user import User
from app.models.course import Course, Module, Lesson
from app.models.enrollment import Enrollment, LessonProgress
from app.models.payment import Payment
from app.models.group import Group, GroupMember, Message
from app.models.instructor import InstructorProfile
from app.models.streak import UserStreakRecord
from app.models.article import Article
from app.models.career import JobPosting, JobApplication
from app.models.practice import PracticeLab, PracticeSession
from app.models.challenge import Challenge, ChallengeLeaderboard
from app.models.certification import Certification, UserCertification

__all__ = [
    "Base",
    "TimeStampedModel",
    "User",
    "Course",
    "Module",
    "Lesson",
    "Enrollment",
    "LessonProgress",
    "Payment",
    "Group",
    "GroupMember",
    "Message",
    "InstructorProfile",
    "UserStreakRecord",
    "Article",
    "JobPosting",
    "JobApplication",
    "PracticeLab",
    "PracticeSession",
    "Challenge",
    "ChallengeLeaderboard",
    "Certification",
    "UserCertification",
]
