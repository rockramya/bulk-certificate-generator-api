import copy


def test_rejects_empty_recipient_list(client, job_payload):
    payload = {**job_payload, "recipients": []}

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422
    assert any("recipients" in str(error["loc"]) for error in response.json()["detail"])


def test_rejects_invalid_email_without_creating_job(client, job_payload):
    payload = copy.deepcopy(job_payload)
    payload["recipients"][0]["email"] = "not-an-email"

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_rejects_blank_recipient_name(client, job_payload):
    payload = copy.deepcopy(job_payload)
    payload["recipients"][0]["name"] = "  "

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422