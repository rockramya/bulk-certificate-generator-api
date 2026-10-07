from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Certificate,
    CertificateStatus,
    GenerationJob,
    JobStatus,
)
from app.services.certificate_generator import generate_certificate_pdf


def process_job(
    job_id: str,
    session_factory: sessionmaker[Session],
    storage_dir: Path,
) -> None:
    with session_factory() as session:
        job = session.get(GenerationJob, job_id)
        if job is None:
            return

        job.status = JobStatus.PROCESSING
        session.commit()

        certificate_ids = session.scalars(
            select(Certificate.id)
            .where(Certificate.job_id == job_id)
            .order_by(Certificate.created_at, Certificate.id)
        ).all()

        for certificate_id in certificate_ids:
            certificate = session.get(Certificate, certificate_id)
            job = session.get(GenerationJob, job_id)
            if certificate is None or job is None:
                continue

            output_path = storage_dir / job_id / f"{certificate.id}.pdf"
            try:
                generate_certificate_pdf(
                    recipient_name=certificate.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    issuer_name=job.issuer_name,
                    output_path=output_path,
                )
                certificate.status = CertificateStatus.COMPLETED
                certificate.file_path = str(output_path)
                job.completed_count += 1
            except Exception as error:
                certificate.status = CertificateStatus.FAILED
                certificate.error_message = str(error) or "PDF generation failed"
                job.failed_count += 1
            finally:
                job.processed_count += 1
                session.commit()

        job = session.get(GenerationJob, job_id)
        if job is not None:
            job.status = (
                JobStatus.COMPLETED_WITH_ERRORS
                if job.failed_count
                else JobStatus.COMPLETED
            )
            job.completed_at = datetime.now(timezone.utc)
            session.commit()