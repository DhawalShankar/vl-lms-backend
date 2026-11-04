from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import require_role
from app.core.database import get_db
from app.models.career import JobApplication, JobPosting
from app.models.user import User
from app.schemas.career import JobApplyRequest, JobPostingCreate, JobPostingOut

router = APIRouter()

DEFAULT_JOBS = [
    {
        "id": "job-1",
        "title": "Curriculum Designer (Vernacular Languages)",
        "team": "Education & Linguistics",
        "type": "Full-time / Remote",
        "location": "Remote (India)",
        "emoji": "📚",
        "description": "Design pedagogical frameworks and lesson plans for regional vernacular language learners.",
        "requirements": ["Native fluency in at least 2 Indian languages", "3+ years curriculum design experience"],
        "apply_email": "support@cosmoindiaprakashan.in",
        "is_active": True,
    },
    {
        "id": "job-2",
        "title": "AI/ML Speech Engineer (Indian Languages)",
        "team": "Voice AI Engineering",
        "type": "Full-time",
        "location": "Remote / Bengaluru",
        "emoji": "🤖",
        "description": "Fine-tune acoustic models and phoneme recognition pipelines for Indian accents and dialects.",
        "requirements": ["Experience with PyTorch, Whisper, Wav2Vec", "Audio signal processing"],
        "apply_email": "support@cosmoindiaprakashan.in",
        "is_active": True,
    },
    {
        "id": "job-3",
        "title": "Language Mentor & Quality Evaluator",
        "team": "Content Verification",
        "type": "Contract / Flexible",
        "location": "Pan-India Remote",
        "emoji": "✍️",
        "description": "Review student audio recordings and provide feedback on pronunciation accuracy.",
        "requirements": ["Certified language instructor", "Clear spoken diction and phonetic knowledge"],
        "apply_email": "support@cosmoindiaprakashan.in",
        "is_active": True,
    },
]


@router.get(
    "/jobs",
    response_model=List[JobPostingOut],
    summary="List all active career openings",
)
def list_jobs(db: Session = Depends(get_db)):
    try:
        jobs = db.query(JobPosting).filter(JobPosting.is_active == True).all()
        if jobs:
            return [
                JobPostingOut(
                    id=str(j.id),
                    title=j.title,
                    team=j.team,
                    type=j.type,
                    location=j.location,
                    emoji=j.emoji,
                    description=j.description,
                    requirements=j.requirements or [],
                    apply_email=j.apply_email,
                    is_active=j.is_active,
                )
                for j in jobs
            ]
    except Exception:
        pass

    return [JobPostingOut(**j) for j in DEFAULT_JOBS]


@router.post(
    "/jobs",
    response_model=JobPostingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job posting (Admin only)",
)
def create_job(
    payload: JobPostingCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    job = JobPosting(
        title=payload.title,
        team=payload.team,
        type=payload.type,
        location=payload.location,
        emoji=payload.emoji,
        description=payload.description,
        requirements=payload.requirements,
        apply_email=payload.apply_email,
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobPostingOut(
        id=str(job.id),
        title=job.title,
        team=job.team,
        type=job.type,
        location=job.location,
        emoji=job.emoji,
        description=job.description,
        requirements=job.requirements or [],
        apply_email=job.apply_email,
        is_active=job.is_active,
    )


@router.post(
    "/apply",
    status_code=status.HTTP_201_CREATED,
    summary="Submit an application for a job opening",
)
def apply_for_job(
    payload: JobApplyRequest,
    db: Session = Depends(get_db),
):
    application = JobApplication(
        job_id=payload.job_id,
        applicant_name=payload.applicant_name,
        applicant_email=payload.applicant_email,
        resume_url=payload.resume_url,
        cover_note=payload.cover_note,
    )
    db.add(application)
    db.commit()

    return {
        "success": True,
        "message": "Application submitted successfully. Our talent team will review your profile.",
    }

