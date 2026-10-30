from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .analysis import analyze_with_ai
from .intelligence import (
    build_intelligence,
    match_job_description,
    rewrite_bullet,
    compare_resumes,
)
from .parser import extract_resume_text
from .report import build_analysis_report
from .schemas import (
    AnalysisRequest,
    AnalysisResult,
    BulletRewriteRequest,
    JobMatchRequest,
)

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Elevix Career Intelligence", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze/text", response_model=AnalysisResult)
def analyze_text(request: AnalysisRequest) -> AnalysisResult:
    return analyze_with_ai(request.resume_text, request.target_role)


@app.post("/api/analyze/file", response_model=AnalysisResult)
async def analyze_file(
    file: UploadFile = File(...),
    target_role: str | None = Form(default=None),
) -> AnalysisResult:
    text = await extract_resume_text(file)
    return analyze_with_ai(text, target_role)


@app.post("/api/intelligence")
def career_intelligence(request: AnalysisRequest) -> dict:
    return build_intelligence(request.resume_text, request.target_role)


@app.post("/api/intelligence/file")
async def career_intelligence_file(
    file: UploadFile = File(...),
    target_role: str | None = Form(default=None, max_length=100),
) -> dict:
    text = await extract_resume_text(file)
    return build_intelligence(text, target_role)


@app.post("/api/job-match")
def job_match(request: JobMatchRequest) -> dict:
    return match_job_description(request.resume_text, request.job_description)


@app.post("/api/job-match/file")
async def job_match_file(
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=50, max_length=20_000),
) -> dict:
    resume_text = await extract_resume_text(file)
    return match_job_description(resume_text, job_description)


@app.post("/api/rewrite-bullet")
def bullet_rewrite(request: BulletRewriteRequest) -> dict:
    return rewrite_bullet(request.bullet)


@app.post("/api/interview")
def interview_questions(request: AnalysisRequest) -> dict:
    result = build_intelligence(request.resume_text, request.target_role)
    return {
        "questions": result["interview_questions"],
        "mode": result["mode"],
        "disclaimer": "Questions are generated from resume text and a role template; they are not an assessment of interview performance.",
    }


@app.post("/api/compare")
async def compare_resume_versions(
    first_file: UploadFile | None = File(default=None),
    second_file: UploadFile | None = File(default=None),
    first_text: str | None = Form(default=None, max_length=50_000),
    second_text: str | None = Form(default=None, max_length=50_000),
) -> dict:
    if first_file is not None:
        first = await extract_resume_text(first_file)
    else:
        first = (first_text or "").strip()
    if second_file is not None:
        second = await extract_resume_text(second_file)
    else:
        second = (second_text or "").strip()
    if len(first) < 50 or len(second) < 50:
        raise HTTPException(
            status_code=422,
            detail="Provide two resumes, each with at least 50 readable characters.",
        )
    return compare_resumes(first[:50_000], second[:50_000])


@app.post("/api/report")
def create_report(analysis: AnalysisResult) -> Response:
    return Response(
        content=build_analysis_report(analysis),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=elevix-report.pdf"},
    )


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")
