import os
from pathlib import Path

from fastapi import FastAPI

from app.api import certificates, jobs
from app.database import create_database_engine, create_session_factory
from app.models import Base


def create_app(
    database_url: str | None = None,
    storage_dir: str | Path | None = None,
) -> FastAPI:
    project_root = Path(__file__).resolve().parent.parent
    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", f"sqlite:///{project_root / 'certificates.db'}"
    )
    resolved_storage_dir = Path(
        storage_dir or os.getenv("CERTIFICATE_STORAGE_DIR", project_root / "storage" / "certificates")
    ).resolve()
    resolved_storage_dir.mkdir(parents=True, exist_ok=True)

    engine = create_database_engine(resolved_database_url)
    Base.metadata.create_all(engine)

    application = FastAPI(
        title="Bulk Certificate Generator",
        description="Generate and retrieve certificates through background jobs.",
        version="1.0.0",
    )
    application.state.engine = engine
    application.state.session_factory = create_session_factory(engine)
    application.state.storage_dir = resolved_storage_dir
    application.include_router(jobs.router)
    application.include_router(certificates.router)

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()