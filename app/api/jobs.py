from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Certificate, CertificateStatus, GenerationJob, JobStatus
from app.schemas import (
    CertificateResult,
    JobCreateRequest,
    JobCreatedResponse,
    JobResponse,
)
from app.services.job_processor import process_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _certificate_result(certificate: Certificate) -> CertificateResult:
    download_url = (
        f"/api/certificates/{certificate.id}"
        if certificate.status == CertificateStatus.COMPLETED
        else None
    )
    return CertificateResult(
        id=certificate.id,
        recipient_name=certificate.recipient_name,
        recipient_email=certificate.recipient_email,
        status=certificate.status.value,
        error_message=certificate.error_message,
        download_url=download_url,
    )


@router.post("/", response_model=JobCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_db),
) -> JobCreatedResponse:
    job = GenerationJob(
        event_name=payload.event_name,
        event_date=payload.event_date,
        issuer_name=payload.issuer_name,
        status=JobStatus.PENDING,
        total_count=len(payload.recipients),
    )
    job.certificates = [
        Certificate(recipient_name=recipient.name.strip(), recipient_email=recipient.email)
        for recipient in payload.recipients
    ]
    session.add(job)
    session.commit()
    session.refresh(job)

    background_tasks.add_task(
        process_job,
        job.id,
        request.app.state.session_factory,
        Path(request.app.state.storage_dir),
    )
    return JobCreatedResponse(
        id=job.id,
        status=job.status.value,
        total_count=job.total_count,
        status_url=f"/api/jobs/{job.id}",
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, session: Session = Depends(get_db)) -> JobResponse:
    job = session.get(GenerationJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")

    certificates = session.scalars(
        select(Certificate)
        .where(Certificate.job_id == job_id)
        .order_by(Certificate.created_at, Certificate.id)
    ).all()
    progress = job.processed_count / job.total_count * 100 if job.total_count else 100.0
    return JobResponse(
        id=job.id,
        status=job.status.value,
        total_count=job.total_count,
        completed_count=job.completed_count,
        failed_count=job.failed_count,
        processed_count=job.processed_count,
        progress_percentage=round(progress, 2),
        created_at=job.created_at,
        completed_at=job.completed_at,
        certificates=[_certificate_result(certificate) for certificate in certificates],
    )


@router.get("/{job_id}/certificates", response_model=list[CertificateResult])
def list_job_certificates(
    job_id: str, session: Session = Depends(get_db)
) -> list[CertificateResult]:
    if session.get(GenerationJob, job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    certificates = session.scalars(
        select(Certificate)
        .where(Certificate.job_id == job_id)
        .order_by(Certificate.created_at, Certificate.id)
    ).all()
    return [_certificate_result(certificate) for certificate in certificates]