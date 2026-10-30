from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)
RESUME_V1 = """Alex Student
alex@example.com
+1 555 123 4567
Summary
Computer Science student with Python, SQL, React, Git, and communication skills.
Education
BSc Computer Science, 2025
Projects
Built a student portal using React and Python.
Experience
Developed a data dashboard during an internship.
"""
RESUME_V2 = """Alex Student
alex@example.com
+1 555 123 4567
Summary
Computer Science student with Python, SQL, React, Git, Docker, and communication skills.
Education
BSc Computer Science, 2025
Skills
Python, SQL, React, Git, Docker
Projects
Built a student portal using React and Python.
Experience
Developed a data dashboard during an internship.
"""
JOB_DESCRIPTION = """We are looking for a Software Developer with Python, SQL, Git, and Docker experience.
Build and maintain reliable software with a collaborative engineering team."""


def _pdf_resume(text: str) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output)
    y = 800
    for line in text.splitlines():
        pdf.drawString(40, y, line)
        y -= 18
    pdf.save()
    return output.getvalue()


def _docx_resume(text: str) -> bytes:
    output = BytesIO()
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(output)
    return output.getvalue()


def test_intelligence_returns_transparent_career_sections():
    response = client.post(
        "/api/intelligence",
        json={"resume_text": RESUME_V2, "target_role": "Software Developer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "Rule-based analysis"
    assert body["career_dna"]["interpretation"].startswith("These are resume evidence")
    assert sum(item["max_score"] for item in body["ats"]["categories"]) == 100
    assert body["ats"]["score"] == sum(item["score"] for item in body["ats"]["categories"])
    assert "Formatting signals" in {item["name"] for item in body["ats"]["categories"]}
    assert "specific ATS" in body["ats"]["disclaimer"]
    assert all(item["improvement"] for item in body["ats"]["deductions"])
    assert body["readiness"]["categories"][-1]["score"] is None
    assert "interview preparation cannot be measured" in body["readiness"]["formula"].lower()
    assert body["roadmap"]["days_90"]["milestones"]
    assert body["roadmap"]["learning_topics"]
    assert body["roadmap"]["portfolio_projects"]
    assert body["interview_questions"]
    assert any("student portal" in item["question"] for item in body["interview_questions"])


def test_readiness_does_not_count_an_unselected_role_as_zero():
    response = client.post("/api/intelligence", json={"resume_text": RESUME_V2})
    assert response.status_code == 200
    body = response.json()
    compatibility = next(
        category
        for category in body["readiness"]["categories"]
        if category["name"] == "Target-role compatibility"
    )
    assert compatibility["score"] is None
    assert body["readiness"]["score"] > 0


def test_interview_endpoint_returns_resume_grounded_questions():
    response = client.post(
        "/api/interview",
        json={"resume_text": RESUME_V2, "target_role": "Software Developer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "Rule-based analysis"
    assert any("Python" in item["question"] for item in body["questions"])


def test_job_match_scores_detected_overlap_and_explains_formula():
    response = client.post(
        "/api/job-match",
        json={"resume_text": RESUME_V2, "job_description": JOB_DESCRIPTION},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] > 0
    assert {"Python", "SQL", "Git"} <= set(body["matched_skills"])
    assert "55%" in body["calculation"]
    assert body["mode"] == "Rule-based comparison"
    assert body["role_recommendations"][0]["role"] == "Software Developer"
    assert "Projects" not in body["relevant_experience"]["evidence"]


def test_bullet_rewrite_does_not_invent_metrics():
    bullet = "Worked on a Python dashboard for student attendance"
    response = client.post("/api/rewrite-bullet", json={"bullet": bullet})
    assert response.status_code == 200
    body = response.json()
    assert any("Contributed to" in item["text"] for item in body["versions"])
    assert all("42%" not in item["text"] for item in body["versions"])
    assert "No metric was invented" in body["metric_prompt"]

    invalid = client.post("/api/rewrite-bullet", json={"bullet": "----------"})
    assert invalid.status_code == 422


def test_resume_comparison_identifies_skills_and_sections():
    response = client.post(
        "/api/compare",
        data={"first_text": RESUME_V1, "second_text": RESUME_V2},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Docker" in body["added_skills"]
    assert "skills" in body["added_sections"]
    assert any("Docker" in item for item in body["added_content"])
    assert body["summary"]


def test_pdf_and_docx_resume_uploads_are_parsed():
    pdf_response = client.post(
        "/api/intelligence/file",
        files={"file": ("resume.pdf", _pdf_resume(RESUME_V2), "application/pdf")},
        data={"target_role": "Software Developer"},
    )
    docx_response = client.post(
        "/api/intelligence/file",
        files={
            "file": (
                "resume.docx",
                _docx_resume(RESUME_V2),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"target_role": "Software Developer"},
    )
    assert pdf_response.status_code == 200
    assert docx_response.status_code == 200
    assert "Python" in pdf_response.json()["analysis"]["skills"]["technical"]
    assert "Python" in docx_response.json()["analysis"]["skills"]["technical"]


def test_job_match_accepts_uploaded_resume():
    response = client.post(
        "/api/job-match/file",
        files={"file": ("resume.docx", _docx_resume(RESUME_V2), "application/octet-stream")},
        data={"job_description": JOB_DESCRIPTION},
    )
    assert response.status_code == 200
    assert "Python" in response.json()["matched_skills"]


def test_resume_comparison_accepts_two_uploaded_versions():
    response = client.post(
        "/api/compare",
        files=[
            ("first_file", ("old.docx", _docx_resume(RESUME_V1), "application/octet-stream")),
            ("second_file", ("new.docx", _docx_resume(RESUME_V2), "application/octet-stream")),
        ],
    )
    assert response.status_code == 200
    assert "Docker" in response.json()["added_skills"]
