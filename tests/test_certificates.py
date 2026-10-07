def test_lists_and_downloads_generated_certificates(client, job_payload):
    created = client.post("/api/jobs/", json=job_payload).json()

    response = client.get(f"{created['status_url']}/certificates")

    assert response.status_code == 200
    certificates = response.json()
    assert len(certificates) == 2
    assert all(certificate["status"] == "COMPLETED" for certificate in certificates)

    download = client.get(certificates[0]["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")


def test_missing_job_and_certificate_return_404(client):
    assert client.get("/api/jobs/not-a-job").status_code == 404
    assert client.get("/api/certificates/not-a-certificate").status_code == 404