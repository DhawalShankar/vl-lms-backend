from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
import uuid6
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_optional_current_user, require_role
from app.core.database import get_db
from app.models.course import Course, Lesson, Module
from app.models.enrollment import Enrollment
from app.models.group import Group, GroupMember
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


def _build_course_out(c: Course, db: Session) -> CourseOut:
    modules_count = len(c.modules)
    lessons_count = sum(len(m.lessons) for m in c.modules)
    enrolled_count = len(c.enrollments) if c.enrollments else 0
    is_pub = (c.status == "published")

    # Parse stored resources
    raw_resources = getattr(c, "resources", None) or []
    resources = [
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
        resources=resources,
        instructor_id=c.instructor_id,
        instructor=InstructorPublic(
            id=c.instructor.id,
            full_name=c.instructor.full_name,
            avatar_url=c.instructor.avatar_url,
        ),
        status=c.status,
        modules_count=modules_count,
        lessons_count=lessons_count,
        enrolledCount=enrolled_count,
        enrolled_count=enrolled_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


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

    # If course is draft or archived, only creator or admin can view it
    if course.status != "published":
        if not current_user or (
            current_user.id != course.instructor_id and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or is currently not published.",
            )

    # Determine full access: creator, admin, or actively enrolled student
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
                    Enrollment.status == "active",
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
            can_access = has_full_access or l.is_preview
            lessons_out.append(
                LessonOut(
                    id=l.id,
                    module_id=l.module_id,
                    title=l.title,
                    description=l.description,
                    youtube_video_id=l.youtube_video_id if can_access else None,
                    notes_url=l.notes_url if can_access else None,
                    order_index=l.order_index,
                    is_preview=l.is_preview,
                    is_unlocked=can_access,
                    created_at=l.created_at,
                    updated_at=l.updated_at,
                )
            )
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

    enrolled_count = len(course.enrollments) if course.enrollments else 0
    is_pub = (course.status == "published")

    raw_resources = getattr(course, "resources", None) or []
    resources = [
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
        resources=resources,
        instructor_id=course.instructor_id,
        instructor=InstructorPublic(
            id=course.instructor.id,
            full_name=course.instructor.full_name,
            avatar_url=course.instructor.avatar_url,
        ),
        status=course.status,
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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this course")

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
    course.resources = current_res
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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this course")

    current_res = list(getattr(course, "resources", None) or [])
    filtered_res = [r for r in current_res if r.get("id") != resource_id]
    course.resources = filtered_res
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
    Creates a new course in published or draft mode as requested.
    Automatically provisions companion private Course Group and educator cohort.
    """
    course_status = "published" if payload.isPublished else "draft"

    # Serialize resources list
    raw_resources = [r.model_dump() for r in payload.resources] if payload.resources else []

    course = Course(
        instructor_id=current_user.id,
        title=payload.title,
        description=payload.description,
        language=payload.language,
        level=payload.level,
        category=payload.category,
        duration=payload.duration,
        thumbnail_url=payload.thumbnail_url,
        price=payload.price,
        status=course_status,
        is_featured=payload.is_featured or False,
        tags=payload.tags or [],
        resources=raw_resources,
    )
    db.add(course)
    db.flush()

    # Auto-create the companion course discussion group
    course_group = Group(
        name=f"{course.title} — Cohort",
        description=f"Official private discussion group for students enrolled in {course.title}.",
        group_type="course",
        language=course.language,
        course_id=course.id,
        created_by=current_user.id,
    )
    db.add(course_group)
    db.flush()

    # Add instructor as administrator of this group
    group_member = GroupMember(
        group_id=course_group.id,
        user_id=current_user.id,
        role="admin",
    )
    db.add(group_member)

    # If requested modules count > 0, provision initial module structure
    modules_to_create = payload.modules or 0
    if modules_to_create > 0:
        for idx in range(1, min(modules_to_create + 1, 15)):
            mod = Module(
                course_id=course.id,
                title=f"Module {idx}: Core Foundations & Practice",
                description="Structured lessons, pronunciation exercises, and study notes.",
                order_index=idx,
            )
            db.add(mod)

    db.commit()
    db.refresh(course)

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
    """Returns all courses (draft, published, archived) created by the instructor."""
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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")

    update_data = payload.model_dump(exclude_unset=True)

    # Handle isPublished / is_published boolean updates
    if "isPublished" in update_data and update_data["isPublished"] is not None:
        course.status = "published" if update_data["isPublished"] else "draft"
        del update_data["isPublished"]
    if "is_published" in update_data and update_data["is_published"] is not None:
        course.status = "published" if update_data["is_published"] else "draft"
        del update_data["is_published"]

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


@router.patch(
    "/{course_id}/status",
    response_model=CourseOut,
    summary="Change course status (draft, published, archived)",
)
def set_course_status(
    course_id: UUID,
    payload: CourseStatusUpdate,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to change course status")

    course.status = payload.status
    db.commit()
    db.refresh(course)

    return _build_course_out(course, db)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course and all associated modules and lessons",
)
def delete_course(
    course_id: UUID,
    current_user: User = Depends(require_role(["instructor", "admin"])),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this course")

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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this course")

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

    if module.course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this module")

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

    if module.course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this module")

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

    if module.course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this module")

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

    return LessonOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        youtube_video_id=lesson.youtube_video_id,
        notes_url=lesson.notes_url,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview,
        is_unlocked=True,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


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

    if lesson.module.course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this lesson")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    return LessonOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        youtube_video_id=lesson.youtube_video_id,
        notes_url=lesson.notes_url,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview,
        is_unlocked=True,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


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

    if lesson.module.course.instructor_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this lesson")

    db.delete(lesson)
    db.commit()
    return None
