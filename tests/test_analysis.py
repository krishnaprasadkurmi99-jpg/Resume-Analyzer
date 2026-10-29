from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
RESUME = """Alex Student
Computer Science student with Python, SQL, React, Git, and communication skills.
Built a student portal project and completed an internship working with data."""


def test_text_analysis_returns_structured_result():
    response = client.post("/api/analyze/text", json={"resume_text": RESUME})
    assert response.status_code == 200
    body = response.json()
    assert "Python" in body["skills"]["technical"]
    assert body["job_recommendations"][0]["suitability_score"] >= 0
    assert body["disclaimer"]


def test_short_text_is_rejected():
    response = client.post("/api/analyze/text", json={"resume_text": "too short"})
    assert response.status_code == 422


def test_invalid_file_type_is_rejected():
    response = client.post(
        "/api/analyze/file",
        files={"file": ("resume.txt", b"some resume content " * 10, "text/plain")},
    )
    assert response.status_code == 415


def test_report_download_returns_pdf():
    analysis = client.post("/api/analyze/text", json={"resume_text": RESUME}).json()
    response = client.post("/api/report", json=analysis)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.content.startswith(b"%PDF")
