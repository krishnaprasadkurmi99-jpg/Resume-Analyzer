from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .analysis import analyze_with_ai
from .parser import extract_resume_text
from .report import build_analysis_report
from .schemas import AnalysisRequest, AnalysisResult

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Placement Resume Analyzer", version="1.0.0")
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


@app.post("/api/report")
def create_report(analysis: AnalysisResult) -> Response:
    return Response(
        content=build_analysis_report(analysis),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=career-lens-report.pdf"},
    )


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")
