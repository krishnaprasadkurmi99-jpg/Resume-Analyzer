from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnalysisRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=50_000)
    target_role: str | None = Field(default=None, max_length=100)


class JobMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=50_000)
    job_description: str = Field(..., min_length=50, max_length=20_000)


class BulletRewriteRequest(BaseModel):
    bullet: str = Field(..., min_length=10, max_length=1_000)

    @field_validator("bullet")
    @classmethod
    def require_bullet_text(cls, value: str) -> str:
        cleaned = value.strip().strip(" •-\t")
        if len(cleaned) < 10 or not any(character.isalnum() for character in cleaned):
            raise ValueError("Provide a resume bullet with at least 10 meaningful characters.")
        return cleaned


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
