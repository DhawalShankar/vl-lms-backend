# app/api/v1/endpoints/courses.py
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user, require_role
from app.core.database import get_db
from app.models.course import Course, Lesson, Module
from app.models.enrollment import Enrollment
from app.models.group import Group, GroupMember
from app.models.payment import Payment
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseDetailOut,
    CourseOut,
    CourseResource,
    CourseResourceCreate,
    CourseStatusUpdate,
    CourseUpdate,
    InstructorLanguageSummary,
    InstructorPublic,
    LanguageSummary,
    LessonCreate,
    LessonOut,
    LessonUpdate,
    ModuleCreate,
    ModuleOut,
    ModuleUpdate,
)

router = APIRouter()

STANDARD_VERNACULAR_LANGUAGES = [
    "Hindi", "English", "Tamil", "Telugu", "Bengali", "Marathi",
    "Gujarati", "Kannada", "Malayalam", "Punjabi", "Odia", "Assamese", "Urdu", "Sanskrit"
]

# While a course is live or waiting for review, instructors cannot change it.
# They must move it back to draft first (which takes it offline until it is approved again).
LOCKED_STATUSES = {"published", "pending_review"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _active_enrolled(course: Course) -> int:
    """Enrollments that count (cancelled ones, e.g. from a deleted student, do not)."""
    return sum(1 for e in (course.enrollments or []) if e.status != "cancelled")


def mark_published(course: Course, admin_id: UUID) -> None:
    """Single place that publishes a course. Only admins ever call this."""
    course.status = "published"
    course.published_by = admin_id
    course.reviewed_by = admin_id
    course.reviewed_at = _now()
    course.rejection_reason = None


def _parse_resources(course: Course) -> List[CourseResource]:
    """Turn the stored JSON resources into CourseResource objects."""
    raw_resources = getattr(course, "resources", None) or []
    return [
        CourseResource(
            id=r.get("id", f"res-{i}"),
            type=r.get("type", "video"),
            title=r.get("title", "Resource"),
            url=r.get("url", ""),
            duration=r.get("duration"),
            description=r.get("description"),
        )
        for i, r in enumerate(raw_resources)
    ]


def _build_course_out(c: Course, db: Session) -> CourseOut:
    modules_count = len(c.modules)
    lessons_count = sum(len(m.lessons) for m in c.modules)
    enrolled_count = _active_enrolled(c)
    is_pub = (c.status == "published")

    return CourseOut(
        id=c.id,
        _id=str(c.id),
        title=c.title,
        description=c.description,
        language=c.language,
        level=c.level,
        category=getattr(c, "category", "grammar") or "grammar",
        duration=getattr(c, "duration", "8 Weeks") or "8 Weeks",
        thumbnail_url=c.thumbnail_url,
        price=c.price,
        is_free=c.is_free,
        isPublished=is_pub,
        is_published=is_pub,
        is_featured=getattr(c, "is_featured", False) or False,
        tags=getattr(c, "tags", None) or [],
        resources=_parse_resources(c),
        instructor_id=c.instructor_id,
        instructor=InstructorPublic(
            id=c.instructor.id,
            full_name=c.instructor.full_name,
            avatar_url=c.instructor.avatar_url,
        ),
        status=c.status,
        rejection_reason=c.rejection_reason,
        submitted_at=c.submitted_at,
        managed_by_admin=c.managed_by_admin,
        modules_count=modules_count,
        lessons_count=lessons_count,
        enrolledCount=enrolled_count,
        enrolled_count=enrolled_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _lesson_out(lesson: Lesson, unlocked: bool = True) -> LessonOut:
    return LessonOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        youtube_video_id=lesson.youtube_video_id if unlocked else None,
        notes_url=lesson.notes_url if unlocked else None,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview,
        is_unlocked=unlocked,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


def _authorize_course(course: Course, user: User, action: str = "modify", edit: bool = True) -> None:
    """
    Ownership + approval rules.
    - Only the owner or an admin can touch a course.
    - edit=True (content/price/curriculum changes): instructors are blocked while the course is
      live or in review, and always on admin-managed courses. Admins are never blocked.
    """
    if course.instructor_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail=f"Not authorized to {action} this course")
    if user.role == "admin":
        return
    if course.managed_by_admin:
        raise HTTPException(
            status_code=403,
            detail="This course is managed by an admin. Contact support to change it.",
        )
    if edit and course.status in LOCKED_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="This course is live or in review. Move it back to draft to edit it.",
        )


def _get_owned_course(
    db: Session, course_id: UUID, current_user: User, action: str = "modify", edit: bool = True
) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _authorize_course(course, current_user, action, edit)
    return course


def create_course_record(
    db: Session,
    payload: CourseCreate,
    instructor_id: UUID,
    status_value: str,
    created_by: UUID,
    managed_by_admin: bool = False,
) -> Course:
    """Creates the course, its companion group and starter modules. Used by instructors and by admins."""
    raw_resources = [r.model_dump() for r in payload.resources] if payload.resources else []

    course = Course(
        instructor_id=instructor_id,
        title=payload.title,
        description=payload.description,
        language=payload.language,
        level=payload.level,
        category=payload.category,
        duration=payload.duration,
        thumbnail_url=payload.thumbnail_url,
        price=payload.price,
        status="draft",
        is_featured=payload.is_featured or False,
        tags=payload.tags or [],
        resources=raw_resources,
        created_by=created_by,
        managed_by_admin=managed_by_admin,
    )
    db.add(course)
    db.flush()

    if status_value == "published":
        mark_published(course, created_by)

    # Auto-create the companion course discussion group; the instructor administers it
    course_group = Group(
        name=f"{course.title} — Cohort",
        description=f"Official private discussion group for students enrolled in {course.title}.",
        group_type="course",
        language=course.language,
        course_id=course.id,
        created_by=instructor_id,
    )
    db.add(course_group)
    db.flush()

    db.add(GroupMember(group_id=course_group.id, user_id=instructor_id, role="admin"))

    modules_to_create = payload.modules or 0
    if modules_to_create > 0:
        for idx in range(1, min(modules_to_create + 1, 15)):
            db.add(
                Module(
                    course_id=course.id,
                    title=f"Module {idx}: Core Foundations & Practice",
                    description="Structured lessons, pronunciation exercises, and study notes.",
                    order_index=idx,
                )
            )

    db.commit()
    db.refresh(course)
    return course


# ============================================================================
# 1. HIERARCHY & DISCOVERY ENDPOINTS (Public / Student)
# ============================================================================

@router.get(
    "/languages",
    response_model=List[LanguageSummary],
    summary="Top-level: List all available languages with active course counts",
)
def get_available_languages(db: Session = Depends(get_db)):
    """
    Returns languages that have published courses, enriched with standard
    vernacular tracks so catalog directories always display active tracks.
    """
    results = (
        db.query(Course.language, func.count(Course.id).label("count"))
        .filter(Course.status == "published")
        .group_by(Course.language)
        .order_by(func.count(Course.id).desc())
        .all()
    )

    db_counts = {lang.title(): count for lang, count in results}

    # Ensure all primary vernacular tracks are represented
    summary_map = {}
    for lang in STANDARD_VERNACULAR_LANGUAGES:
        summary_map[lang] = db_counts.get(lang, 0)

    # Add any extra custom languages from database
    for lang, count in db_counts.items():
        if lang not in summary_map:
            summary_map[lang] = count

    return [
        LanguageSummary(language=lang, course_count=count)
        for lang, count in summary_map.items()
    ]


@router.get(
    "/instructors",
    response_model=List[InstructorLanguageSummary],
    summary="Second-level: List instructors teaching a language",
)
def get_instructors_by_language(
    language: Optional[str] = Query(None, description="Filter instructors by language"),
    db: Session = Depends(get_db),
):
    """
    Returns instructors who have published courses.
    Optionally filters by language to show teachers in that specific language domain.
    """
    query = (
        db.query(
            User.id.label("instructor_id"),
            User.full_name,
            User.avatar_url,
            func.count(Course.id).label("course_count"),
        )
        .join(Course, Course.instructor_id == User.id)
        .filter(Course.status == "published")
    )

    if language:
        query = query.filter(Course.language.ilike(language))

    query = (
        query.group_by(User.id, User.full_name, User.avatar_url)
        .order_by(func.count(Course.id).desc())
    )

    results = query.all()
    return [
        InstructorLanguageSummary(
            instructor_id=row.instructor_id,
            full_name=row.full_name,
            avatar_url=row.avatar_url,
            course_count=row.course_count,
        )
        for row in results
    ]


@router.get(
    "",
    response_model=List[CourseOut],
    summary="Browse course catalog with multi-dimensional filtering",
)
def list_published_courses(
    language: Optional[str] = Query(None, description="Filter by language (e.g. Hindi, Tamil)"),
    instructor_id: Optional[UUID] = Query(None, description="Filter by teacher"),
    level: Optional[str] = Query(None, description="Filter by level (foundation, intermediate, etc.)"),
    category: Optional[str] = Query(None, description="Filter by category (grammar, conversation, etc.)"),
    featured: Optional[bool] = Query(None, description="Filter featured courses"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Browse published course cards.
    Supports filtering by language, instructor, level, category, and featured status.
    """
    query = db.query(Course).filter(Course.status == "published")

    if language:
        query = query.filter(Course.language.ilike(language))
    if instructor_id:
        query = query.filter(Course.instructor_id == instructor_id)
    if level:
        query = query.filter(Course.level.ilike(level))
    if category:
        query = query.filter(Course.category.ilike(category))
    if featured is not None:
        query = query.filter(Course.is_featured == featured)

    courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_course_out(c, db) for c in courses]


@router.get(
    "/{course_id}",
    response_model=CourseDetailOut,
    summary="Get course detail & syllabus with Content Gatekeeper protection",
)
def get_course_detail(
    course_id: UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full course information including syllabus (modules and lessons).
    Enforces the Content Gatekeeper rule:
    - YouTube video IDs and Drive notes are masked as null for non-preview lessons
      unless the student is enrolled, the owner, or an admin.
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    # Draft, in-review, rejected or archived: only the creator or an admin can view it
    if course.status != "published":
        if not current_user or (
            current_user.id != course.instructor_id and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or is currently not published.",
            )

    # Determine full access: creator, admin, or an enrolled student (active or completed)
    has_full_access = False
    if current_user:
        if current_user.id == course.instructor_id or current_user.role == "admin":
            has_full_access = True
        else:
            enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.course_id == course.id,
                    Enrollment.user_id == current_user.id,
                    Enrollment.status.in_(["active", "completed"]),
                )
                .first()
            )
            if enrollment:
                has_full_access = True

    # Process modules & lessons through Content Gatekeeper
    modules_out: List[ModuleOut] = []
    total_lessons = 0

    for m in course.modules:
        lessons_out: List[LessonOut] = []
        for l in m.lessons:
            total_lessons += 1
            lessons_out.append(_lesson_out(l, unlocked=has_full_access or l.is_preview))
        modules_out.append(
            ModuleOut(
                id=m.id,
                course_id=m.course_id,
                title=m.title,
                description=m.description,
                order_index=m.order_index,
                lessons=lessons_out,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )

    enrolled_count = _active_enrolled(course)
    is_pub = (course.status == "published")

    return CourseDetailOut(
        id=course.id,
        _id=str(course.id),
        title=course.title,
        description=course.description,
        language=course.language,
        level=course.level,
        category=getattr(course, "category", "grammar") or "grammar",
        duration=getattr(course, "duration", "8 Weeks") or "8 Weeks",
        thumbnail_url=course.thumbnail_url,
        price=course.price,
        is_free=course.is_free,
        isPublished=is_pub,
        is_published=is_pub,
        is_featured=getattr(course, "is_featured", False) or False,
        tags=getattr(course, "tags", None) or [],
        resources=_parse_resources(course),
        instructor_id=course.instructor_id,
        instructor=InstructorPublic(
            id=course.instructor.id,
            full_name=course.instructor.full_name,
            avatar_url=course.instructor.avatar_url,
        ),
        status=course.status,
        rejection_reason=course.rejection_reason,
        submitted_at=course.submitted_at,
        managed_by_admin=course.managed_by_admin,
        modules_count=len(modules_out),
        lessons_count=total_lessons,
        enrolledCount=enrolled_count,
        enrolled_count=enrolled_count,
        modules=modules_out,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


# ============================================================================
# 2. COURSE RESOURCES ENDPOINTS
# ============================================================================

@router.get(
    "/{course_id}/resources",
    response_model=List[CourseResource],
    summary="Get resources and study materials for a course",
)
def get_course_resources(
    course_id: UUID,
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _parse_resources(course)


@router.post(
    "/{course_id}/resources",
    response_model=CourseResource,
    status_code=status.HTTP_201_CREATED,
    summary="Add a study material or AI lab redirect to a course",
)
def add_course_resource(
    course_id: UUID,
    payload: CourseResourceCreate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(db, course_id, current_user)

    new_id = f"res-{int(datetime.now().timestamp() * 1000)}"
    new_res = {
        "id": new_id,
        "type": payload.type,
        "title": payload.title,
        "url": payload.url,
        "duration": payload.duration,
        "description": payload.description,
    }

    current_res = list(getattr(course, "resources", None) or [])
    current_res.append(new_res)
    course.resources = current_res  # reassign so SQLAlchemy detects the JSON change
    db.commit()
    db.refresh(course)

    return CourseResource(**new_res)


@router.delete(
    "/{course_id}/resources/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resource item from a course",
)
def delete_course_resource(
    course_id: UUID,
    resource_id: str,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(db, course_id, current_user)

    current_res = list(getattr(course, "resources", None) or [])
    course.resources = [r for r in current_res if r.get("id") != resource_id]
    db.commit()
    return None


# ============================================================================
# 3. INSTRUCTOR STUDIO ENDPOINTS (Course Management)
# ============================================================================

@router.post(
    "",
    response_model=CourseDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course (Instructor/Admin only)",
)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    """
    Instructors always create drafts (the isPublished flag is ignored for them): publishing
    needs admin approval. Admins can create a published course directly.
    Automatically provisions companion private Course Group and educator cohort.
    """
    publish_now = current_user.role == "admin" and bool(payload.isPublished)

    course = create_course_record(
        db,
        payload,
        instructor_id=current_user.id,
        status_value="published" if publish_now else "draft",
        created_by=current_user.id,
    )
    return get_course_detail(course_id=course.id, current_user=current_user, db=db)


@router.get(
    "/instructor/mine",
    response_model=List[CourseOut],
    summary="Get all courses taught by the currently logged-in instructor",
)
def get_my_courses(
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    """Returns all courses (draft, in review, published, rejected, archived) of the instructor."""
    courses = (
        db.query(Course)
        .filter(Course.instructor_id == current_user.id)
        .order_by(Course.created_at.desc())
        .all()
    )
    return [_build_course_out(c, db) for c in courses]


@router.put(
    "/{course_id}",
    response_model=CourseDetailOut,
    summary="Update course metadata (Creator or Admin only)",
)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(db, course_id, current_user, action="edit")
    is_admin = current_user.role == "admin"

    update_data = payload.model_dump(exclude_unset=True)

    # `modules` is a relationship on Course (not a count) and `status` is changed
    # only via the status / submit / approval endpoints, so never copy them with setattr below.
    update_data.pop("modules", None)
    update_data.pop("status", None)

    # isPublished / is_published: only admins may publish this way
    wants_publish: Optional[bool] = None
    for key in ("isPublished", "is_published"):
        if key in update_data:
            value = update_data.pop(key)
            if value is not None:
                wants_publish = value
    if wants_publish is not None:
        if is_admin:
            if wants_publish:
                mark_published(course, current_user.id)
            else:
                course.status = "draft"
        elif wants_publish:
            raise HTTPException(
                status_code=403,
                detail="Publishing needs admin approval. Use Submit for review.",
            )

    if not is_admin:
        update_data.pop("is_featured", None)

    # Handle resources list serialization
    if "resources" in update_data and update_data["resources"] is not None:
        update_data["resources"] = [
            r if isinstance(r, dict) else r.model_dump()
            for r in update_data["resources"]
        ]

    for field, value in update_data.items():
        if hasattr(course, field):
            setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return get_course_detail(course_id=course.id, current_user=current_user, db=db)


@router.post(
    "/{course_id}/submit",
    response_model=CourseOut,
    summary="Submit a draft (or rejected) course for admin review",
)
def submit_for_review(
    course_id: UUID,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the course owner can submit it for review")
    if course.managed_by_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="This course is managed by an admin.")
    if course.status not in ("draft", "rejected"):
        raise HTTPException(
            status_code=409,
            detail=f"Only draft or rejected courses can be submitted (this one is {course.status}).",
        )

    lesson_count = (
        db.query(Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .filter(Module.course_id == course.id)
        .count()
    )
    if lesson_count < 1:
        raise HTTPException(status_code=400, detail="Add at least one lesson before submitting for review.")

    course.status = "pending_review"
    course.submitted_at = _now()
    course.rejection_reason = None
    db.commit()
    db.refresh(course)
    return _build_course_out(course, db)


@router.patch(
    "/{course_id}/status",
    response_model=CourseOut,
    summary="Change course status. Instructors can only move a course back to draft.",
)
def set_course_status(
    course_id: UUID,
    payload: CourseStatusUpdate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(
        db, course_id, current_user, action="change the status of", edit=False
    )

    target = payload.status
    if current_user.role != "admin" and target != "draft":
        raise HTTPException(
            status_code=403,
            detail="Only an admin can publish or archive a course. Use Submit for review to request publishing.",
        )

    if target == "published":
        mark_published(course, current_user.id)
    else:
        course.status = target
    db.commit()
    db.refresh(course)

    return _build_course_out(course, db)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course (archived instead if it has students or payments)",
)
def delete_course(
    course_id: UUID,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(db, course_id, current_user, action="delete", edit=False)
    is_admin = current_user.role == "admin"

    if not is_admin and course.status not in ("draft", "rejected"):
        raise HTTPException(
            status_code=409,
            detail="Move the course back to draft before deleting it.",
        )

    has_enrollments = (
        db.query(Enrollment.id).filter(Enrollment.course_id == course.id).first() is not None
    )
    has_payments = db.query(Payment.id).filter(Payment.course_id == course.id).first() is not None

    if has_enrollments or has_payments:
        if not is_admin:
            raise HTTPException(
                status_code=409,
                detail="This course has students or payments, so it cannot be deleted. Ask an admin to archive it.",
            )
        course.status = "archived"
        db.commit()
        return None

    db.delete(course)
    db.commit()
    return None


# ============================================================================
# 4. CURRICULUM BUILDER: MODULES
# ============================================================================

@router.post(
    "/{course_id}/modules",
    response_model=ModuleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a module to a course",
)
def create_module(
    course_id: UUID,
    payload: ModuleCreate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    _get_owned_course(db, course_id, current_user)

    existing_count = db.query(Module).filter(Module.course_id == course_id).count()
    order_index = payload.order_index if payload.order_index > 1 else (existing_count + 1)

    module = Module(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        order_index=order_index,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@router.put(
    "/modules/{module_id}",
    response_model=ModuleOut,
    summary="Update a module title or order",
)
def update_module(
    module_id: UUID,
    payload: ModuleUpdate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    module = db.get(Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    _authorize_course(module.course, current_user, "modify")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(module, field, value)

    db.commit()
    db.refresh(module)
    return module


@router.delete(
    "/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a module and its lessons",
)
def delete_module(
    module_id: UUID,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    module = db.get(Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    _authorize_course(module.course, current_user, "modify")

    db.delete(module)
    db.commit()
    return None


# ============================================================================
# 5. CURRICULUM BUILDER: LESSONS
# ============================================================================

@router.post(
    "/modules/{module_id}/lessons",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a lesson to a module",
)
def create_lesson(
    module_id: UUID,
    payload: LessonCreate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    module = db.get(Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    _authorize_course(module.course, current_user, "modify")

    existing_count = db.query(Lesson).filter(Lesson.module_id == module_id).count()
    order_index = payload.order_index if payload.order_index > 1 else (existing_count + 1)

    lesson = Lesson(
        module_id=module_id,
        title=payload.title,
        description=payload.description,
        youtube_video_id=payload.youtube_video_id,
        notes_url=payload.notes_url,
        order_index=order_index,
        is_preview=payload.is_preview,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return _lesson_out(lesson)


@router.put(
    "/lessons/{lesson_id}",
    response_model=LessonOut,
    summary="Update lesson content or preview toggle",
)
def update_lesson(
    lesson_id: UUID,
    payload: LessonUpdate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    _authorize_course(lesson.module.course, current_user, "modify")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    return _lesson_out(lesson)


@router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lesson",
)
def delete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    _authorize_course(lesson.module.course, current_user, "modify")

    db.delete(lesson)
    db.commit()
    return None