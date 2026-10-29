from typing import Literal

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=50_000)
    target_role: str | None = Field(default=None, max_length=100)


class JobRecommendation(BaseModel):
    role: str
    suitability_score: int = Field(ge=0, le=100)
    reason: str
    required_skills: list[str]


class MissingSkill(BaseModel):
    skill: str
    priority: Literal["Beginner", "Intermediate", "Advanced"]
    reason: str


class LearningSuggestion(BaseModel):
    topic: str
    resources: list[str]
    project_idea: str


class ResumeImprovement(BaseModel):
    section: str
    issue: str
    suggestion: str


class Skills(BaseModel):
    technical: list[str]
    soft: list[str]
    strengths: list[str]


class AnalysisResult(BaseModel):
    resume_summary: str
    skills: Skills
    job_recommendations: list[JobRecommendation]
    missing_skills: list[MissingSkill]
    learning_suggestions: list[LearningSuggestion]
    resume_improvements: list[ResumeImprovement]
    disclaimer: str = (
        "Suitability scores are indicative estimates, not guaranteed hiring probabilities."
    )
