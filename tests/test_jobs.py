def test_create_job_returns_accepted_response(client, job_payload):
    response = client.post("/api/jobs/", json=job_payload)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["total_count"] == 2
    assert body["id"]
    assert body["status_url"] == f"/api/jobs/{body['id']}"


def test_job_status_reports_finished_progress(client, job_payload):
    created = client.post("/api/jobs/", json=job_payload).json()

    response = client.get(created["status_url"])

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["total_count"] == 2
    assert body["completed_count"] == 2
    assert body["failed_count"] == 0
    assert body["processed_count"] == 2
    assert body["progress_percentage"] == 100.0