from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name must not be blank")
        return name


class JobCreateRequest(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    event_date: str = Field(min_length=1, max_length=40)
    issuer_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1, max_length=1000)


class JobStatusValue(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class CertificateStatusValue(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CertificateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_name: str
    recipient_email: str | None
    status: CertificateStatusValue
    error_message: str | None
    download_url: str | None


class JobResponse(BaseModel):
    id: str
    status: JobStatusValue
    total_count: int
    completed_count: int
    failed_count: int
    processed_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: datetime | None
    certificates: list[CertificateResult]


class JobCreatedResponse(BaseModel):
    id: str
    status: JobStatusValue
    total_count: int
    status_url: str