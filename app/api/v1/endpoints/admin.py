from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import require_role
from app.core.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.user import User
from app.schemas.admin import (
    AdminStatsOut,
    AdminUserOut,
    AdminUsersListOut,
    UserRoleUpdate,
    UserStatusUpdate,
)

router = APIRouter()


@router.get(
    "/stats",
    response_model=AdminStatsOut,
    summary="Platform-wide metrics & revenue statistics (Admin only)",
)
def get_platform_stats(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_instructors = db.query(User).filter(User.role == "instructor").count()
    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(Course.status == "published").count()
    total_enrollments = db.query(Enrollment).count()

    total_rev_scalar = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == "paid")
        .scalar()
    )
    gross_revenue = float(total_rev_scalar or 0.0)
    net_payout = round(gross_revenue * 0.85, 2)

    active_languages = (
        db.query(func.count(func.distinct(Course.language)))
        .filter(Course.status == "published")
        .scalar()
        or 0
    )

    return AdminStatsOut(
        total_users=total_users,
        total_students=total_students,
        total_instructors=total_instructors,
        total_courses=total_courses,
        published_courses=published_courses,
        total_enrollments=total_enrollments,
        gross_revenue=gross_revenue,
        net_instructor_payout=net_payout,
        active_languages=active_languages,
    )


@router.get(
    "/users",
    response_model=AdminUsersListOut,
    summary="Paginated user directory with role and status filtering (Admin only)",
)
def list_users(
    role: Optional[str] = Query(None, description="Filter by role: student, instructor, admin"),
    search: Optional[str] = Query(None, description="Search by full_name or email"),
    is_active: Optional[bool] = Query(None, description="Filter active/suspended accounts"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_filter)) | (User.email.ilike(search_filter))
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    users_out = []
    for u in users:
        enrolled_count = len(u.enrollments) if u.enrollments else 0
        taught_count = len(u.courses_taught) if u.courses_taught else 0
        users_out.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                avatar_url=u.avatar_url,
                is_active=u.is_active,
                created_at=u.created_at,
                enrolled_courses_count=enrolled_count,
                courses_taught_count=taught_count,
            )
        )

    return AdminUsersListOut(
        total=total,
        page=page,
        limit=limit,
        users=users_out,
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserOut,
    summary="Promote or demote user role (Admin only)",
)
def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    db.commit()
    db.refresh(user)

    enrolled_count = len(user.enrollments) if user.enrollments else 0
    taught_count = len(user.courses_taught) if user.courses_taught else 0

    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        created_at=user.created_at,
        enrolled_courses_count=enrolled_count,
        courses_taught_count=taught_count,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserOut,
    summary="Suspend or activate a user account (Admin only)",
)
def toggle_user_status(
    user_id: UUID,
    payload: Optional[UserStatusUpdate] = None,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend your own admin account")

    if payload and payload.is_active is not None:
        user.is_active = payload.is_active
    else:
        user.is_active = not user.is_active

    db.commit()
    db.refresh(user)

    enrolled_count = len(user.enrollments) if user.enrollments else 0
    taught_count = len(user.courses_taught) if user.courses_taught else 0

    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        created_at=user.created_at,
        enrolled_courses_count=enrolled_count,
        courses_taught_count=taught_count,
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a user account (Admin only)",
)
def delete_user_account(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    db.delete(user)
    db.commit()
    return None

