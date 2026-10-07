from app.services import job_processor


def test_failed_recipient_does_not_stop_remaining_certificates(
    client, job_payload, monkeypatch
):
    original_generator = job_processor.generate_certificate_pdf

    def fail_for_avery(**kwargs):
        if kwargs["recipient_name"] == "Avery Example":
            raise RuntimeError("simulated PDF failure")
        return original_generator(**kwargs)

    monkeypatch.setattr(job_processor, "generate_certificate_pdf", fail_for_avery)
    created = client.post("/api/jobs/", json=job_payload).json()

    response = client.get(created["status_url"])

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED_WITH_ERRORS"
    assert body["total_count"] == 2
    assert body["completed_count"] == 1
    assert body["failed_count"] == 1
    assert body["processed_count"] == 2
    failed = next(item for item in body["certificates"] if item["recipient_name"] == "Avery Example")
    succeeded = next(item for item in body["certificates"] if item["recipient_name"] == "Jordan Example")
    assert failed["status"] == "FAILED"
    assert failed["error_message"] == "simulated PDF failure"
    assert succeeded["status"] == "COMPLETED"
    assert succeeded["download_url"] is not None