from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=tmp_path / "certificates",
    )
    with TestClient(application) as test_client:
        yield test_client
    application.state.engine.dispose()


@pytest.fixture
def job_payload() -> dict[str, object]:
    return {
        "event_name": "Practical Python Workshop",
        "event_date": "2026-10-07",
        "issuer_name": "Example Academy",
        "recipients": [
            {"name": "Avery Example", "email": "avery@example.com"},
            {"name": "Jordan Example", "email": "jordan@example.com"},
        ],
    }