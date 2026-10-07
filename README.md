# Bulk Certificate Generator

A small FastAPI service that accepts a list of recipients, creates a background generation job, and produces one downloadable PDF certificate per recipient. SQLite stores job and result metadata; PDF files live on local disk.

## Features

- Validate event and recipient input with Pydantic.
- Generate a professional, landscape PDF certificate from one predefined ReportLab template.
- Process each recipient independently and record individual success or failure.
- Track job status, successful count, failed count, processed count, and percentage progress.
- List results and download successful certificates.
- Use FastAPI `BackgroundTasks`; no external queue or service is needed.

## Technology

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy 2 and SQLite
- Pydantic 2
- ReportLab
- Pytest and HTTPX

## Project Structure

```text
app/
  api/
    certificates.py
    jobs.py
  services/
    certificate_generator.py
    job_processor.py
  database.py
  dependencies.py
  main.py
  models.py
  schemas.py
tests/
  conftest.py
  test_certificate_generation.py
  test_certificates.py
  test_job_status.py
  test_jobs.py
  test_validation.py
requirements.txt
README.md
```

Generated files are written to `storage/certificates/` by default. SQLite data is stored in `certificates.db` in the project root. Both are ignored by Git.

## Setup and Installation

Use Python 3.11 or newer. From the project root:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

To use a different database or output folder, set `DATABASE_URL` or `CERTIFICATE_STORAGE_DIR`. The default database URL is SQLite at the project root. The configured storage directory is created automatically.

## Run the API

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive Swagger documentation is at `http://127.0.0.1:8000/docs`; ReDoc is at `http://127.0.0.1:8000/redoc`.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/jobs/` | Validate input, create a job and its recipient records, then schedule processing. Returns `202 Accepted`. |
| `GET` | `/api/jobs/{job_id}` | Return job status, counters, progress, timestamps, and per-recipient results. |
| `GET` | `/api/jobs/{job_id}/certificates` | List recipient certificate results for a job. |
| `GET` | `/api/certificates/{certificate_id}` | Download a completed certificate PDF. |
| `GET` | `/health` | Return a simple health response. |

### Create a Job

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/jobs/ `
  -H "Content-Type: application/json" `
  -d '{"event_name":"Practical Python Workshop","event_date":"2026-10-07","issuer_name":"Example Academy","recipients":[{"name":"Avery Example","email":"avery@example.com"},{"name":"Jordan Example","email":"jordan@example.com"}]}'
```

Example response (`202 Accepted`):

```json
{
  "id": "4d641af2-3f46-4c7a-a531-b4b9db62834c",
  "status": "PENDING",
  "total_count": 2,
  "status_url": "/api/jobs/4d641af2-3f46-4c7a-a531-b4b9db62834c"
}
```

The status may already have advanced by the time it is checked. Poll `GET /api/jobs/{job_id}` for the current state. A completed response resembles:

```json
{
  "id": "4d641af2-3f46-4c7a-a531-b4b9db62834c",
  "status": "COMPLETED",
  "total_count": 2,
  "completed_count": 2,
  "failed_count": 0,
  "processed_count": 2,
  "progress_percentage": 100.0,
  "created_at": "2026-10-07T12:00:00",
  "completed_at": "2026-10-07T12:00:02",
  "certificates": [
    {
      "id": "5ac52740-dccf-451d-bf44-b481724fabcf",
      "recipient_name": "Avery Example",
      "recipient_email": "avery@example.com",
      "status": "COMPLETED",
      "error_message": null,
      "download_url": "/api/certificates/5ac52740-dccf-451d-bf44-b481724fabcf"
    }
  ]
}
```

`completed_count` is successful PDFs; `failed_count` is failed PDFs; `processed_count` is the sum of recipients attempted. Progress is based on `processed_count / total_count`. A job ends as `COMPLETED_WITH_ERRORS` if one or more recipients fail.

### List and Download Certificates

Use `GET /api/jobs/{job_id}/certificates` to list result metadata. Successful entries have a `download_url`; failed and pending entries have no download URL. Download a PDF with:

```powershell
curl.exe -L http://127.0.0.1:8000/api/certificates/5ac52740-dccf-451d-bf44-b481724fabcf -o certificate.pdf
```

An unknown job or certificate returns `404`. A certificate that has not successfully generated returns `409`. A missing file returns `404`.

## Architecture and Processing Flow

1. The jobs route validates the request with Pydantic, stores a `GenerationJob` and one pending `Certificate` per recipient, then returns `202`.
2. FastAPI runs `process_job` as a background task. It opens its own SQLAlchemy session from the app's session factory, independently of the request session.
3. The processor sets the job to `PROCESSING`, then invokes the PDF generator for each certificate. It records and commits that recipient's result before continuing.
4. At the end, the processor sets `COMPLETED` or `COMPLETED_WITH_ERRORS`, records completion time, and leaves results available through the read endpoints.

Routes handle HTTP and response shaping. SQLAlchemy models define persistent state; `job_processor.py` owns lifecycle and per-recipient failure handling; `certificate_generator.py` owns the single ReportLab layout. Each generated file is named with its certificate UUID and stored under the job UUID directory.

## Database Design

`GenerationJob` stores the event, lifecycle status, recipient totals and counters, and timestamps. `Certificate` stores the recipient, individual status, optional file path, and error message, and has a foreign key to its job. Status columns use explicit enum values. UUID strings are the external identifiers.

## Failure Handling

An exception while generating one PDF is caught at that recipient boundary. That record becomes `FAILED` with its error message, the job's failed and processed counts advance, and processing continues. Successful records are retained and downloadable even if other recipients fail. The final job status communicates partial failure without discarding useful results.

## Testing

Tests create a temporary SQLite database and storage directory for each client fixture; no external service is used. The suite covers request creation, input validation, PDF readability and content, progress and lifecycle status, an injected per-recipient PDF failure, certificate listing, and download behavior.

```powershell
pytest
```

## Design Decisions

- A single predefined vector-based ReportLab template keeps output deterministic and avoids a separate template asset or image dependency.
- FastAPI `BackgroundTasks` satisfies the assignment with minimal infrastructure. It is suitable for this local assignment; a durable queue would be a future scaling option.
- Each background invocation creates its own database session. Recipient-level commits make progress/results visible and isolate ordinary PDF-generation failures.
- `processed_count` is separate from successful `completed_count`, so progress reaches 100% even when a recipient fails.
- SQLite and local filesystem storage are the defaults; both are configurable without adding deployment infrastructure.

## Future Improvements

- Add pagination for large result lists and configurable batch limits.
- Add retention/cleanup policies and a storage backend abstraction.
- Add durable queueing and retry policies if jobs must survive process restarts.
- Add structured logging and metrics for operational deployments.