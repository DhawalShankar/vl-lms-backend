# app/api/v1/endpoints/admin.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, distinct, func
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.v1.endpoints.courses import create_course_record, get_course_detail, mark_published
from app.core.database import get_db
from app.models.course import Course, Lesson, Module
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.user import User
from app.schemas.admin import (
    AdminCourseCreate,
    AdminCourseOut,
    AdminInstructorOut,
    AdminStatsOut,
    AdminUserOut,
    CourseRejectIn,
    DeleteCourseOut,
    DeleteUserOut,
    UserStatusUpdate,
)
from app.schemas.course import CourseDetailOut

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================================
# STATS & USERS
# ============================================================================

@router.get(
    "/stats",
    response_model=AdminStatsOut,
    summary="SSO login stats and course counts (Admin only)",
)
def get_platform_stats(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    now = _now()
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    # "Logged in via SSO at least once" = login_count > 0 (dev/mock accounts stay at 0)
    logged_in = db.query(User).filter(User.deleted_at.is_(None), User.login_count > 0)

    role_counts = dict(
        db.query(User.role, func.count(User.id))
        .filter(User.deleted_at.is_(None), User.login_count > 0)
        .group_by(User.role)
        .all()
    )
    courses_by_status = dict(
        db.query(Course.status, func.count(Course.id)).group_by(Course.status).all()
    )

    return AdminStatsOut(
        total_users=logged_in.count(),
        new_users_7d=logged_in.filter(User.first_login_at >= d7).count(),
        active_users_7d=logged_in.filter(User.last_login_at >= d7).count(),
        active_users_30d=logged_in.filter(User.last_login_at >= d30).count(),
        students=role_counts.get("student", 0),
        instructors=role_counts.get("instructor", 0),
        admins=role_counts.get("admin", 0),
        courses_by_status=courses_by_status,
    )


@router.get(
    "/users",
    response_model=List[AdminUserOut],
    summary="User directory (Admin only). Deleted accounts are excluded.",
)
def list_users(
    role: Optional[str] = Query(None, description="student | instructor | admin"),
    search: Optional[str] = Query(None, description="Search by full_name or email"),
    limit: int = Query(500, ge=1, le=1000),
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    query = db.query(User).filter(User.deleted_at.is_(None))
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search}%"
        query = query.filter(User.full_name.ilike(like) | User.email.ilike(like))
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    return [AdminUserOut.model_validate(u) for u in users]


@router.get(
    "/instructors",
    response_model=List[AdminInstructorOut],
    summary="Active instructors, for the 'create course on behalf of' picker (Admin only)",
)
def list_instructors(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .filter(User.deleted_at.is_(None), User.is_active.is_(True), User.role == "instructor")
        .order_by(User.full_name)
        .all()
    )
    return [AdminInstructorOut(id=u.id, full_name=u.full_name, email=u.email) for u in users]


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserOut,
    summary="Suspend or re-activate a user (Admin only)",
)
def toggle_user_status(
    user_id: UUID,
    payload: Optional[UserStatusUpdate] = None,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend your own admin account")

    if payload and payload.is_active is not None:
        user.is_active = payload.is_active
    else:
        user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.delete(
    "/users/{user_id}",
    response_model=DeleteUserOut,
    summary="Delete a user account (soft delete, Admin only)",
)
def delete_user_account(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Soft delete: the row is kept (payments and payouts reference it) but the account is dead.
    - deleted_at is set and is_active turned off, so tokens stop working.
    - /sso/exchange rejects deleted users, so they are NOT re-created on their next login.
    - Name and avatar are cleared. The email is kept on purpose, so the block can match it.
    - Their courses are archived (which also hides their public instructor profile) and their
      active enrollments are cancelled. Completed enrollments and payment records are kept.
    """
    user = db.get(User, user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be deleted here")

    user.deleted_at = _now()
    user.is_active = False
    user.full_name = "Deleted user"
    user.avatar_url = None

    db.query(Course).filter(
        Course.instructor_id == user.id, Course.status != "archived"
    ).update({Course.status: "archived"}, synchronize_session=False)

    db.query(Enrollment).filter(
        Enrollment.user_id == user.id, Enrollment.status == "active"
    ).update({Enrollment.status: "cancelled"}, synchronize_session=False)

    db.commit()
    return DeleteUserOut(ok=True)


# ============================================================================
# COURSES: LIST, REVIEW QUEUE, APPROVE / REJECT / UNPUBLISH, CREATE ON BEHALF, DELETE
# ============================================================================

def _admin_course_query(db: Session):
    return (
        db.query(
            Course,
            User.full_name,
            User.email,
            func.count(distinct(case((Enrollment.status != "cancelled", Enrollment.id)))),
            func.count(distinct(Lesson.id)),
        )
        .join(User, User.id == Course.instructor_id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .outerjoin(Module, Module.course_id == Course.id)
        .outerjoin(Lesson, Lesson.module_id == Module.id)
        .group_by(Course.id, User.full_name, User.email)
    )


def _course_row_out(row) -> AdminCourseOut:
    c, instructor_name, instructor_email, enrolled, lessons = row
    return AdminCourseOut(
        id=c.id,
        title=c.title,
        language=c.language,
        level=c.level,
        status=c.status,
        price=float(c.price or 0),
        enrolled_count=enrolled,
        lessons_count=lessons,
        instructor_id=c.instructor_id,
        instructor_name=instructor_name,
        instructor_email=instructor_email,
        submitted_at=c.submitted_at,
        reviewed_at=c.reviewed_at,
        rejection_reason=c.rejection_reason,
        managed_by_admin=c.managed_by_admin,
        created_at=c.created_at,
    )


def _one_course_out(db: Session, course_id: UUID) -> AdminCourseOut:
    row = _admin_course_query(db).filter(Course.id == course_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Course not found")
    return _course_row_out(row)


@router.get(
    "/courses",
    response_model=List[AdminCourseOut],
    summary="All courses with instructor, price and counts (Admin only)",
)
def list_courses(
    status: Optional[str] = Query(None, description="Filter by status, e.g. pending_review"),
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    query = _admin_course_query(db)
    if status:
        query = query.filter(Course.status == status)
    rows = query.order_by(Course.created_at.desc()).all()
    return [_course_row_out(r) for r in rows]


@router.post(
    "/courses",
    response_model=CourseDetailOut,
    status_code=201,
    summary="Create a course on behalf of an instructor, optionally publishing it (Admin only)",
)
def create_course_for_instructor(
    payload: AdminCourseCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    instructor = db.get(User, payload.instructor_id)
    if not instructor or instructor.deleted_at or instructor.role != "instructor":
        raise HTTPException(status_code=404, detail="Instructor not found")

    course = create_course_record(
        db,
        payload,
        instructor_id=instructor.id,
        status_value="published" if payload.publish else "draft",
        created_by=current_user.id,
        managed_by_admin=True,
    )
    return get_course_detail(course_id=course.id, current_user=current_user, db=db)


@router.post(
    "/courses/{course_id}/approve",
    response_model=AdminCourseOut,
    summary="Approve a course that is waiting for review (publishes it)",
)
def approve_course(
    course_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "pending_review":
        raise HTTPException(status_code=409, detail="Only courses in review can be approved.")

    mark_published(course, current_user.id)
    db.commit()
    return _one_course_out(db, course_id)


@router.post(
    "/courses/{course_id}/reject",
    response_model=AdminCourseOut,
    summary="Reject a course that is waiting for review, with a reason the instructor will see",
)
def reject_course(
    course_id: UUID,
    payload: CourseRejectIn,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "pending_review":
        raise HTTPException(status_code=409, detail="Only courses in review can be rejected.")

    course.status = "rejected"
    course.rejection_reason = payload.reason.strip()
    course.reviewed_by = current_user.id
    course.reviewed_at = _now()
    db.commit()
    return _one_course_out(db, course_id)


@router.post(
    "/courses/{course_id}/unpublish",
    response_model=AdminCourseOut,
    summary="Take a live course offline (back to draft)",
)
def unpublish_course(
    course_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "published":
        raise HTTPException(status_code=409, detail="Only published courses can be unpublished.")

    course.status = "draft"
    db.commit()
    return _one_course_out(db, course_id)


@router.delete(
    "/courses/{course_id}",
    response_model=DeleteCourseOut,
    summary="Delete a course (Admin only). Archived instead if it has enrollments or payments.",
)
def delete_course(
    course_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    has_enrollments = (
        db.query(Enrollment.id).filter(Enrollment.course_id == course.id).first() is not None
    )
    has_payments = db.query(Payment.id).filter(Payment.course_id == course.id).first() is not None

    if has_enrollments or has_payments:
        course.status = "archived"
        db.commit()
        return DeleteCourseOut(archived=True)

    db.delete(course)
    db.commit()
    return DeleteCourseOut(archived=False)