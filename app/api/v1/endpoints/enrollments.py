from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.course import Course, Lesson, Module
from app.models.enrollment import Enrollment, LessonProgress
from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.enrollment import (
    CourseProgressDetail,
    EnrollmentOut,
    LessonProgressToggleResponse,
)

router = APIRouter()


def _get_course_lesson_count(course: Course) -> int:
    """Helper to count total lessons inside a course."""
    return sum(len(m.lessons) for m in course.modules)


def _get_completed_lesson_count(db: Session, user_id: UUID, course: Course) -> int:
    """Helper to count completed lessons by a student for a specific course."""
    lesson_ids = [l.id for m in course.modules for l in m.lessons]
    if not lesson_ids:
        return 0
    return (
        db.query(func.count(LessonProgress.id))
        .filter(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.is_completed == True,
        )
        .scalar()
        or 0
    )


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll student in a course (Unlocks curriculum and course group)",
)
def enroll_in_course(
    course_id: UUID,
    demo_bypass: bool = Query(
        False,
        description="Bypass payment for testing paid courses in development mode",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enrolls the authenticated student into a course:
    - If already enrolled, returns existing enrollment (idempotent).
    - If free course (price = 0) or demo_bypass=True, enrolls immediately.
    - Automatically adds student to the course's private community group.
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.status != "published" and current_user.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot enroll in an unpublished course.",
        )

    # Check if already enrolled
    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if existing_enrollment:
        total = _get_course_lesson_count(course)
        completed = _get_completed_lesson_count(db, current_user.id, course)
        percentage = round((completed / total * 100), 1) if total > 0 else 0.0

        return EnrollmentOut(
            id=existing_enrollment.id,
            course_id=course.id,
            course_title=course.title,
            course_thumbnail_url=course.thumbnail_url,
            course_language=course.language,
            course_level=course.level,
            status=existing_enrollment.status,
            progress_percentage=percentage,
            total_lessons=total,
            completed_lessons=completed,
            enrolled_at=existing_enrollment.enrolled_at,
            completed_at=existing_enrollment.completed_at,
        )

    # Check payment requirements
    if course.price > Decimal("0.00") and not demo_bypass:
        # Paid course requires payment checkout
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Course requires payment of INR {course.price}. Please complete payment checkout.",
        )

    # Create enrollment
    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course.id,
        status="active",
    )
    db.add(enrollment)

    # Automatically add student to companion course group (PRD Section 8.2)
    course_group = (
        db.query(Group)
        .filter(Group.course_id == course.id)
        .first()
    )
    if course_group:
        is_member = (
            db.query(GroupMember)
            .filter(
                GroupMember.group_id == course_group.id,
                GroupMember.user_id == current_user.id,
            )
            .first()
        )
        if not is_member:
            group_member = GroupMember(
                group_id=course_group.id,
                user_id=current_user.id,
                role="member",
            )
            db.add(group_member)

    db.commit()
    db.refresh(enrollment)

    total_lessons = _get_course_lesson_count(course)

    return EnrollmentOut(
        id=enrollment.id,
        course_id=course.id,
        course_title=course.title,
        course_thumbnail_url=course.thumbnail_url,
        course_language=course.language,
        course_level=course.level,
        status=enrollment.status,
        progress_percentage=0.0,
        total_lessons=total_lessons,
        completed_lessons=0,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
    )


@router.get(
    "/mine",
    response_model=List[EnrollmentOut],
    summary="Get all enrolled courses for the logged-in student (Student Dashboard)",
)
def get_my_enrolled_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all courses the student is enrolled in with live completion percentage.
    Powers the 'My Courses' student dashboard.
    """
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == current_user.id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )

    result = []
    for en in enrollments:
        course = en.course
        total = _get_course_lesson_count(course)
        completed = _get_completed_lesson_count(db, current_user.id, course)
        percentage = round((completed / total * 100), 1) if total > 0 else 0.0

        result.append(
            EnrollmentOut(
                id=en.id,
                course_id=course.id,
                course_title=course.title,
                course_thumbnail_url=course.thumbnail_url,
                course_language=course.language,
                course_level=course.level,
                status=en.status,
                progress_percentage=percentage,
                total_lessons=total,
                completed_lessons=completed,
                enrolled_at=en.enrolled_at,
                completed_at=en.completed_at,
            )
        )
    return result


@router.post(
    "/{course_id}/lessons/{lesson_id}/toggle",
    response_model=LessonProgressToggleResponse,
    summary="Toggle lesson completed / uncompleted status",
)
def toggle_lesson_progress(
    course_id: UUID,
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Checks or unchecks a lesson as completed:
    - Recalculates course completion percentage.
    - If 100% completed, automatically updates enrollment status to 'completed'.
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify student is enrolled (or is instructor/admin)
    is_enrolled = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.user_id == current_user.id,
        )
        .first()
    )
    if not is_enrolled and current_user.role not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Must be enrolled in course to track progress.",
        )

    lesson = db.get(Lesson, lesson_id)
    if not lesson or lesson.module.course_id != course_id:
        raise HTTPException(
            status_code=404,
            detail="Lesson does not belong to this course.",
        )

    # Toggle progress record
    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )

    now = datetime.now(timezone.utc)
    if progress:
        # Flip status
        progress.is_completed = not progress.is_completed
        progress.completed_at = now if progress.is_completed else None
        is_completed = progress.is_completed
    else:
        # Create completed record
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            is_completed=True,
            completed_at=now,
        )
        db.add(progress)
        is_completed = True

    db.flush()

    # Recalculate course completion
    total = _get_course_lesson_count(course)
    completed = _get_completed_lesson_count(db, current_user.id, course)
    percentage = round((completed / total * 100), 1) if total > 0 else 0.0
    is_course_finished = total > 0 and completed == total

    # Update enrollment status
    if is_enrolled:
        if is_course_finished:
            is_enrolled.status = "completed"
            is_enrolled.completed_at = now
        else:
            is_enrolled.status = "active"
            is_enrolled.completed_at = None

    db.commit()

    return LessonProgressToggleResponse(
        lesson_id=lesson.id,
        is_completed=is_completed,
        completed_at=progress.completed_at,
        course_progress_percentage=percentage,
        completed_lessons=completed,
        total_lessons=total,
        is_course_completed=is_course_finished,
    )


@router.get(
    "/{course_id}/progress",
    response_model=CourseProgressDetail,
    summary="Get detailed progress for a course (Completed lesson IDs and percentage)",
)
def get_course_progress(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the list of completed lesson IDs and overall completion % for the course.
    Powers the checklist state on the frontend Course Player.
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    total = _get_course_lesson_count(course)
    lesson_ids = [l.id for m in course.modules for l in m.lessons]

    completed_records = (
        db.query(LessonProgress.lesson_id)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.is_completed == True,
        )
        .all()
    )
    completed_ids = [r[0] for r in completed_records]
    completed_count = len(completed_ids)
    percentage = round((completed_count / total * 100), 1) if total > 0 else 0.0

    return CourseProgressDetail(
        course_id=course.id,
        total_lessons=total,
        completed_lessons=completed_count,
        progress_percentage=percentage,
        completed_lesson_ids=completed_ids,
        is_completed=(total > 0 and completed_count == total),
    )
