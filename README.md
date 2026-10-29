# CareerLens Resume Analyzer

CareerLens is a functional, privacy-conscious prototype for a college placement cell. It accepts pasted resume text or PDF/DOCX uploads, detects resume-supported skills, recommends roles, identifies gaps, and produces a learning roadmap and ATS-focused improvement suggestions.

## Features

- **Resume input in two formats:** Upload a PDF or DOCX file, or paste resume text directly into the analyzer.
- **Drag-and-drop upload:** Drop a supported resume into the upload area or browse for a file. Uploads are limited to 5 MB.
- **Target-role analysis:** Select a target role such as Software Developer, Data Analyst, Web Developer, AI/ML Engineer, Cybersecurity Analyst, or Cloud Engineer.
- **Automatic skill detection:** Identifies technical skills and soft skills explicitly present in the supplied resume.
- **Career recommendations:** Suggests up to three suitable job roles and displays an indicative suitability percentage based on detected skills.
- **Strength discovery:** Summarizes the resume and highlights detected strengths.
- **Skill-gap identification:** Lists missing skills for recommended roles with beginner or intermediate priority guidance.
- **Personalized learning roadmap:** Provides learning topics, starter resource ideas, and portfolio project suggestions for identified gaps.
- **ATS-focused resume feedback:** Recommends improvements for the summary, project descriptions, section headings, formatting, and readability.
- **Downloadable PDF report:** Exports the complete analysis, including skills, recommendations, gaps, roadmap, improvements, and the analysis disclaimer.
- **Responsive dashboard:** Presents results in a clear, responsive interface with progress bars, skill pills, status messages, and accessible live feedback.
- **Privacy-conscious processing:** The demo analyzes resumes without persisting uploaded files and clearly labels scores as indicative estimates rather than hiring probabilities.
- **Local demo mode:** Runs without an API key using a deterministic local analyzer, with a clear integration seam for a future AI provider.

## Run locally

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` if you want to configure a future AI provider. The default `mock` mode requires no API key.

4. Start the server:

   ```powershell
   py -m uvicorn app.main:app --reload
   ```

   Open http://127.0.0.1:8000.

## Architecture

- `app/main.py` exposes health, text-analysis, and upload-analysis endpoints and serves the frontend.
- `app/parser.py` validates file extensions/size and extracts PDF/DOCX text.
- `app/analysis.py` contains the deterministic local analyzer. `analyze_with_ai` is the integration seam for an LLM provider that returns the same Pydantic schema.
- `app/schemas.py` validates API input and output shapes.
- `app/static/` contains the responsive dashboard with escaped dynamic rendering and printable report export.

The prototype does not persist uploaded resumes. Scores are indicative estimates and are not hiring probabilities. The analyzer never adds a skill unless it is detected in the supplied resume text.

## Test

```powershell
py -m pytest
```

## API

- `GET /api/health`
- `POST /api/analyze/text` with `{ "resume_text": "...", "target_role": "Data Analyst" }`
- `POST /api/analyze/file` as multipart form data with `file` and optional `target_role`
- `POST /api/report` with an analysis response body to download a generated PDF report

For production, put the API behind HTTPS, configure an allow-list of frontend origins, add authentication/rate limiting, and replace the local adapter with a provider that validates structured JSON before returning it.
