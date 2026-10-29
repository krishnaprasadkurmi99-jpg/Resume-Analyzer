import os
import re
from collections.abc import Iterable

from .schemas import (
    AnalysisResult,
    JobRecommendation,
    LearningSuggestion,
    MissingSkill,
    ResumeImprovement,
    Skills,
)

SKILL_CATALOG = {
    "Python": ("technical", {"data analyst", "ai/ml engineer", "software developer"}),
    "Java": ("technical", {"software developer"}),
    "JavaScript": ("technical", {"web developer", "software developer"}),
    "TypeScript": ("technical", {"web developer", "software developer"}),
    "React": ("technical", {"web developer", "software developer"}),
    "FastAPI": ("technical", {"web developer", "software developer"}),
    "SQL": ("technical", {"data analyst", "software developer"}),
    "Pandas": ("technical", {"data analyst", "ai/ml engineer"}),
    "NumPy": ("technical", {"data analyst", "ai/ml engineer"}),
    "TensorFlow": ("technical", {"ai/ml engineer"}),
    "PyTorch": ("technical", {"ai/ml engineer"}),
    "Docker": ("technical", {"cloud engineer", "software developer"}),
    "AWS": ("technical", {"cloud engineer"}),
    "Azure": ("technical", {"cloud engineer"}),
    "Git": ("technical", {"software developer", "web developer", "cloud engineer"}),
    "Linux": ("technical", {"cybersecurity analyst", "cloud engineer"}),
    "Excel": ("technical", {"data analyst"}),
    "Machine Learning": ("technical", {"ai/ml engineer", "data analyst"}),
    "Communication": ("soft", set()),
    "Teamwork": ("soft", set()),
    "Leadership": ("soft", set()),
    "Problem Solving": ("soft", set()),
}

ROLE_REQUIREMENTS = {
    "Software Developer": ["Python", "Java", "Git", "SQL"],
    "Data Analyst": ["Python", "SQL", "Excel", "Pandas"],
    "Web Developer": ["JavaScript", "React", "TypeScript", "Git"],
    "AI/ML Engineer": ["Python", "Machine Learning", "Pandas", "TensorFlow"],
    "Cybersecurity Analyst": ["Linux", "Python", "Networking", "Security"],
    "Cloud Engineer": ["Linux", "Docker", "AWS", "Git"],
}


def _found_skills(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    technical: list[str] = []
    soft: list[str] = []
    for skill, (category, _) in SKILL_CATALOG.items():
        if re.search(rf"(?<!\w){re.escape(skill.lower())}(?!\w)", lowered):
            (technical if category == "technical" else soft).append(skill)
    return technical, soft


def _recommendations(technical: list[str], target_role: str | None) -> list[JobRecommendation]:
    roles: Iterable[str] = ROLE_REQUIREMENTS
    if target_role:
        matching = [role for role in ROLE_REQUIREMENTS if target_role.lower() in role.lower()]
        roles = matching or roles
    recommendations = []
    for role in roles:
        required = ROLE_REQUIREMENTS[role]
        matched = [skill for skill in required if skill in technical]
        score = round(len(matched) / len(required) * 100)
        recommendations.append(
            JobRecommendation(
                role=role,
                suitability_score=score,
                reason=(
                    f"{len(matched)} of {len(required)} common skills were found in the resume."
                    if matched
                    else "This role is a possible path; build the listed foundational skills."
                ),
                required_skills=required,
            )
        )
    return sorted(recommendations, key=lambda item: item.suitability_score, reverse=True)[:3]


def analyze_resume(resume_text: str, target_role: str | None = None) -> AnalysisResult:
    technical, soft = _found_skills(resume_text)
    recommendations = _recommendations(technical, target_role)
    missing: list[MissingSkill] = []
    for recommendation in recommendations:
        for skill in recommendation.required_skills:
            if skill not in technical and not any(item.skill == skill for item in missing):
                priority = "Beginner" if not technical else "Intermediate"
                missing.append(
                    MissingSkill(
                        skill=skill,
                        priority=priority,
                        reason=f"Common requirement for {recommendation.role}.",
                    )
                )
    missing = missing[:8]
    learning = [
        LearningSuggestion(
            topic=item.skill,
            resources=[
                f"{item.skill} beginner documentation",
                f"Hands-on {item.skill} course or tutorial",
            ],
            project_idea=f"Build a small portfolio project using {item.skill} and document your decisions.",
        )
        for item in missing[:5]
    ]
    improvements = [
        ResumeImprovement(
            section="Summary",
            issue="The summary should make the target role and strongest evidence easy to find.",
            suggestion="Lead with your current status, target role, and two resume-supported strengths.",
        ),
        ResumeImprovement(
            section="Projects",
            issue="Project bullets may not communicate contribution and outcomes clearly.",
            suggestion="Use action verbs, name the tools used, and add measurable results only when they are accurate.",
        ),
        ResumeImprovement(
            section="ATS readability",
            issue="Automated screeners work best with consistent headings and simple formatting.",
            suggestion="Use standard section names, text-based contact details, and avoid tables, icons, and text embedded in images.",
        ),
    ]
    strengths = technical[:4] or ["Resume content is ready for skills discovery"]
    return AnalysisResult(
        resume_summary=(
            f"The resume contains {len(technical)} technical and {len(soft)} soft skills. "
            "The recommendations below are based only on skills detected in the supplied text."
        ),
        skills=Skills(technical=technical, soft=soft, strengths=strengths),
        job_recommendations=recommendations,
        missing_skills=missing,
        learning_suggestions=learning,
        resume_improvements=improvements,
    )


def analyze_with_ai(resume_text: str, target_role: str | None = None) -> AnalysisResult:
    # A deterministic local analyzer keeps the prototype usable without credentials.
    # An LLM adapter can replace this function when AI_PROVIDER is configured.
    return analyze_resume(resume_text, target_role)
