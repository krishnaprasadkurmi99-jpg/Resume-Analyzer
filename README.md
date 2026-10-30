# Elevix – Career Intelligence

Elevix is a privacy-conscious resume analysis and career-planning prototype for students and early-career candidates. It combines resume parsing, transparent rule-based checks, job-description comparisons, and practical preparation tools in a responsive dashboard.

## Features

- **Resume analysis:** Paste resume text or upload a PDF/DOCX file (up to 5 MB).
- **Career DNA evidence profile:** Visualizes resume-detected technical skills, project and communication evidence, and related indicators. These are text evidence indicators, not verified or measured proficiency.
- **ATS-style breakdown:** Scores common structure, section completeness, role keyword and skill coverage, experience descriptions, contact details, and education. It is a transparent heuristic, not the score of any particular ATS.
- **Job match simulator:** Compares resume text to a pasted job description, showing catalogued skills, missing skills, related resume lines, and keyword overlap. The score is a text comparison, not a hiring prediction.
- **Placement-readiness snapshot:** Summarizes resume quality, role skill coverage, and project evidence. Interview preparation is explicitly unassessed and excluded from the score because it cannot be measured from a resume.
- **Interview practice:** Creates technical, project, scenario, and HR questions from resume text and a selected role, with suggested answer structures.
- **Learning roadmap:** Organizes detected role skill gaps into a rule-based 30/60/90-day outline with weekly milestones.
- **Grounded bullet rewrites:** Offers wording variations based on an existing bullet. It does not create achievements or metrics; users must verify every claim.
- **Resume version comparison:** Compares two uploaded PDF/DOCX versions for checklist score, recognized skills, and standard section headings.
- **PDF report export:** Downloads the existing summary, skills, recommendations, gaps, and improvement suggestions.
- **Responsive glassmorphism dashboard:** Includes mobile navigation, dark/light themes, accessible status feedback, and responsive insight visualizations.
- **Privacy-conscious processing:** The demo does not persist uploaded resumes and does not require an API key.

All analysis is labeled **Rule-based**. No external AI service is configured, and the application does not claim that a language model performed the analysis. Catalog coverage is intentionally limited; an undetected keyword does not prove a candidate lacks a skill.

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

3. Start the server:

   ```powershell
   py -m uvicorn app.main:app --reload
   ```

4. Open http://127.0.0.1:8000.

## Architecture

- `app/main.py` exposes health, text/file analysis, career intelligence, job match, bullet rewrite, interview practice, resume comparison, and report endpoints.
- `app/parser.py` validates PDF/DOCX extension and size, extracts readable text, and retains line boundaries for section checks.
- `app/analysis.py` contains the existing deterministic skill discovery, recommendations, gap identification, and improvement suggestions.
- `app/intelligence.py` contains explainable career evidence, ATS-style, job-match, readiness, roadmap, interview, rewrite, and comparison heuristics.
- `app/schemas.py` validates API input and output shapes.
- `app/report.py` generates the PDF analysis report.
- `app/static/` contains the responsive glassmorphism interface.

## API

- `GET /api/health`
- `POST /api/analyze/text` with `{ "resume_text": "...", "target_role": "Data Analyst" }`
- `POST /api/analyze/file` as multipart form data with `file` and optional `target_role`
- `POST /api/intelligence` with resume text and optional target role
- `POST /api/intelligence/file` as multipart form data with `file` and optional `target_role`
- `POST /api/job-match` with `{ "resume_text": "...", "job_description": "..." }`
- `POST /api/job-match/file` as multipart form data with `file` and `job_description`
- `POST /api/rewrite-bullet` with `{ "bullet": "..." }`
- `POST /api/interview` with resume text and optional target role
- `POST /api/compare` with two multipart files (`first_file`, `second_file`) or two text fields (`first_text`, `second_text`)
- `POST /api/report` with an analysis response body to download a generated PDF report

## Tests

```powershell
py -m pytest
```

For production, deploy behind HTTPS, configure allowed origins, add authentication and rate limiting, and review the limits of all heuristic scores before using them in high-stakes decisions.
