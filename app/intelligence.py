import re

from .analysis import ROLE_REQUIREMENTS, SKILL_CATALOG, analyze_resume
from .schemas import LearningSuggestion

SECTION_PATTERNS = {
    "experience": r"(?:professional\s+)?experience|employment|internship|work\s+history",
    "education": r"education|academic\s+background|coursework",
    "skills": r"(?:technical\s+)?skills|technologies|competencies",
    "projects": r"(?:selected\s+)?projects|portfolio",
    "summary": r"summary|profile|objective|about\s+me",
}
CONTACT_PATTERNS = {
    "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "phone": r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
}
ACTION_VERBS = {
    "built", "created", "designed", "developed", "implemented", "improved",
    "analyzed", "automated", "led", "managed", "launched", "optimized",
    "tested", "deployed", "delivered", "maintained", "wrote", "reduced",
    "increased", "configured", "integrated", "proposed", "researched",
}
PROGRAMMING_LANGUAGES = {"Python", "Java", "JavaScript", "TypeScript"}
ROLE_ALIASES = {
    "cybersecurity analyst": "Cybersecurity Analyst",
    "ai/ml engineer": "AI/ML Engineer",
    "software developer": "Software Developer",
    "data analyst": "Data Analyst",
    "web developer": "Web Developer",
    "cloud engineer": "Cloud Engineer",
}


def _has_section(text: str, pattern: str) -> bool:
    return bool(
        re.search(rf"(?im)^\s*(?:{pattern})\s*:?\s*$", text)
        or re.search(rf"(?im)^\s*(?:{pattern})\s*:\s*\S.*$", text)
    )


def _is_section_heading(line: str) -> bool:
    return any(_has_section(line, pattern) for pattern in SECTION_PATTERNS.values())


def _role_name(target_role: str | None) -> str | None:
    if not target_role:
        return None
    return next(
        (name for alias, name in ROLE_ALIASES.items() if alias in target_role.lower()),
        None,
    )


def _role_coverage(text: str, target_role: str | None) -> tuple[int, list[str], list[str]]:
    role = _role_name(target_role)
    requirements = ROLE_REQUIREMENTS.get(role or "", [])
    found = {skill.lower() for skill in analyze_resume(text, role).skills.technical}
    matched = [skill for skill in requirements if skill.lower() in found]
    missing = [skill for skill in requirements if skill.lower() not in found]
    score = round(len(matched) / len(requirements) * 100) if requirements else 0
    return score, matched, missing


def _ats_analysis(text: str, target_role: str | None = None) -> dict:
    lowered = text.lower()
    sections = {name: _has_section(text, pattern) for name, pattern in SECTION_PATTERNS.items()}
    contact = {
        name: bool(re.search(pattern, text, re.IGNORECASE))
        for name, pattern in CONTACT_PATTERNS.items()
    }
    role_score, matched, _ = _role_coverage(text, target_role)
    role = _role_name(target_role)
    formatting_flags = []
    if "\t" in text:
        formatting_flags.append("Tab characters may indicate column-based layout.")
    if any(len(line) > 240 for line in text.splitlines()):
        formatting_flags.append("A text line exceeds 240 characters and may be difficult to scan.")
    if re.search(r" {4,}", text):
        formatting_flags.append("Repeated spaces may be used for visual alignment.")
    categories = [
        {
            "name": "Structure",
            "score": round(sum(sections.values()) / len(sections) * 12),
            "max_score": 12,
            "detail": f"{sum(sections.values())} of {len(sections)} standard sections detected.",
        },
        {
            "name": "Section completeness",
            "score": round(
                (sum(sections[name] for name in ("experience", "education", "skills", "projects")) / 4) * 18
            ),
            "max_score": 18,
            "detail": "Checks for experience, education, skills, and projects headings.",
        },
        {
            "name": "Keyword relevance",
            "score": round(role_score * 0.18) if role else min(len(analyze_resume(text).skills.technical) * 4, 18),
            "max_score": 18,
            "detail": (
                f"{len(matched)} target-role skills detected."
                if role
                else "Based on the variety of recognized technical skills; no target role selected."
            ),
        },
        {
            "name": "Skills relevance",
            "score": round(role_score * 0.15) if role else min(len(analyze_resume(text).skills.technical) * 3, 15),
            "max_score": 15,
            "detail": f"{len(matched)} of {len(ROLE_REQUIREMENTS.get(role or '', []))} target-role skills detected."
            if role
            else f"{len(analyze_resume(text).skills.technical)} technical skills detected.",
        },
        {
            "name": "Experience descriptions",
            "score": (
                min(10 + len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text)) * 2, 15)
                if sections["experience"] and re.search(r"\b(" + "|".join(ACTION_VERBS) + r")\b", lowered)
                else 8 if sections["experience"] else 0
            ),
            "max_score": 15,
            "detail": "Looks for an experience section, action verbs, and numeric evidence.",
        },
        {
            "name": "Formatting signals",
            "score": max(10 - len(formatting_flags) * 3, 0),
            "max_score": 10,
            "detail": " ".join(formatting_flags)
            or "No obvious text-extraction formatting flags; visual page layout cannot be assessed from text alone.",
        },
        {
            "name": "Contact information",
            "score": round(sum(contact.values()) / 2 * 6),
            "max_score": 6,
            "detail": f"{sum(contact.values())} of 2 contact details detected (email and phone).",
        },
        {
            "name": "Education",
            "score": 6 if sections["education"] else 0,
            "max_score": 6,
            "detail": "Education heading detected." if sections["education"] else "Education heading not detected.",
        },
    ]
    improvement_tips = {
        "Structure": "Use concise, standard section headings and arrange sections in a clear reading order.",
        "Section completeness": "Add any applicable experience, education, skills, and projects sections.",
        "Keyword relevance": "Tailor truthful skills and terminology to the selected role.",
        "Skills relevance": "Show role-relevant skills in a dedicated section and support them with examples.",
        "Experience descriptions": "Use clear action-led bullets and include outcomes only when you can verify them.",
        "Formatting signals": "Use simple text layout, avoid tabs or spacing for columns, and check the exported document visually.",
        "Contact information": "Include a readable email address and phone number in the resume text.",
        "Education": "Add a clearly labeled education section if applicable.",
    }
    deductions = [
        {
            "category": category["name"],
            "points": category["max_score"] - category["score"],
            "reason": category["detail"],
            "improvement": improvement_tips[category["name"]],
        }
        for category in categories
        if category["score"] < category["max_score"]
    ]
    return {
        "score": sum(category["score"] for category in categories),
        "categories": categories,
        "deductions": deductions,
        "disclaimer": "This transparent heuristic is not a score from any specific ATS platform.",
    }


def _career_dna(text: str, target_role: str | None) -> dict:
    analysis = analyze_resume(text, target_role)
    technical = analysis.skills.technical
    lower = text.lower()
    project_lines = [
        line.strip(" •-\t")
        for line in text.splitlines()
        if line.strip()
        and not _is_section_heading(line)
        and re.search(r"\b(project|built|developed|implemented|created)\b", line, re.I)
    ]
    evidence = [
        {
            "name": "Technical skill breadth",
            "score": min(len(technical) * 12, 100),
            "evidence": f"{len(technical)} recognized technical skills explicitly mentioned.",
        },
        {
            "name": "Programming indicators",
            "score": min(sum(skill in technical for skill in PROGRAMMING_LANGUAGES) * 25, 100),
            "evidence": ", ".join(skill for skill in PROGRAMMING_LANGUAGES if skill in technical)
            or "No catalogued programming language detected.",
        },
        {
            "name": "Problem-solving indicators",
            "score": 75 if "problem solving" in lower or "problem-solving" in lower else 35 if project_lines else 0,
            "evidence": "Problem-solving phrase detected."
            if "problem solving" in lower or "problem-solving" in lower
            else f"{len(project_lines)} project/action evidence lines found."
            if project_lines
            else "No project or problem-solving evidence detected.",
        },
        {
            "name": "Communication indicators",
            "score": 70 if "communication" in lower or "presented" in lower else 35 if "teamwork" in lower else 0,
            "evidence": "Communication-related wording detected in the supplied text."
            if re.search(r"\b(communication|presented|presentation|teamwork)\b", lower)
            else "No communication-related wording detected.",
        },
        {
            "name": "Domain expertise indicators",
            "score": min(sum(skill in technical for skill in analysis.skills.technical) * 10, 100),
            "evidence": f"{len(technical)} technology/domain terms found in the skill catalog.",
        },
        {
            "name": "Project experience",
            "score": min(len(project_lines) * 25, 100),
            "evidence": f"{len(project_lines)} lines containing project/action terms found.",
        },
    ]
    return {
        "indicators": evidence,
        "strengths": analysis.skills.strengths,
        "technical_skills": technical,
        "soft_skills": analysis.skills.soft,
        "interpretation": "These are resume evidence coverage indicators, not measured proficiency or verified ability.",
    }


def _readiness(text: str, target_role: str | None, ats: dict) -> dict:
    role_score, matched, missing = _role_coverage(text, target_role)
    role = _role_name(target_role)
    requirements = ROLE_REQUIREMENTS.get(role or "", [])
    technical_count = len(analyze_resume(text, role).skills.technical)
    technical_score = (
        min(round(technical_count / max(len(requirements), 1) * 100), 100)
        if role
        else min(technical_count * 12, 100)
    )
    lines = [line for line in text.splitlines() if line.strip() and not _is_section_heading(line)]
    project_score = min(
        sum(bool(re.search(r"\b(project|built|developed|implemented|created)\b", line, re.I)) for line in lines) * 25,
        100,
    )
    categories = [
        {"name": "Resume quality", "score": ats["score"], "status": "assessed"},
        {"name": "Technical skills", "score": technical_score, "status": "resume evidence only"},
        {
            "name": "Target-role compatibility",
            "score": role_score if role else None,
            "status": "assessed" if role else "select a target role",
        },
        {"name": "Project evidence", "score": project_score, "status": "resume evidence only"},
        {"name": "Interview preparation", "score": None, "status": "not measurable from a resume"},
    ]
    assessable = [item["score"] for item in categories if item["score"] is not None]
    score = round(sum(assessable) / len(assessable)) if assessable else 0
    strengths = []
    weaknesses = []
    if ats["score"] >= 65:
        strengths.append("The resume includes a substantial set of standard sections and contact evidence.")
    else:
        weaknesses.append("Improve resume structure and completeness using the ATS breakdown.")
    if role and role_score >= 50:
        strengths.append(f"{len(matched)} listed skills align with the {role} role profile.")
    elif role:
        weaknesses.append(f"Only {len(matched)} of {len(matched) + len(missing)} listed {role} skills were detected.")
    else:
        weaknesses.append("Choose a target role to assess role-specific compatibility.")
    priorities = [
        f"Build evidence for {skill} through a project or coursework."
        for skill in missing[:3]
    ]
    if not priorities and ats["score"] < 100:
        priorities = ats["deductions"][:3]
    return {
        "score": score,
        "categories": categories,
        "strengths": strengths or ["Your resume is ready for more role-specific evidence."],
        "weaknesses": weaknesses or ["No major gap was identified by these limited resume checks."],
        "priorities": priorities,
        "formula": "Mean of assessed resume quality, technical-skill evidence, target-role compatibility (missing role skills reduce this), and project evidence. Unassessed categories are excluded; interview preparation cannot be measured from a resume.",
        "disclaimer": "An indicative resume-evidence checklist, not a prediction of placement or interview performance.",
    }


def _roadmap(
    target_role: str | None,
    missing: list[str],
    learning_suggestions: list[LearningSuggestion],
) -> dict:
    skills = missing or [item.topic for item in learning_suggestions] or [
        "Build a role-aligned portfolio project",
        "Practice explaining project decisions",
    ]
    learning_topics = [
        {"topic": item.topic, "resources": item.resources}
        for item in learning_suggestions
    ]
    portfolio_projects = [item.project_idea for item in learning_suggestions]
    if not portfolio_projects:
        portfolio_projects = [
            "Build and document a small portfolio project aligned with your target role."
        ]
    milestones = []
    for index, skill in enumerate(skills[:6]):
        week = index + 1
        milestones.append({
            "week": week,
            "focus": skill,
            "task": f"Study {skill}, complete a hands-on exercise, and record evidence of what you built.",
        })
    return {
        "target_role": _role_name(target_role) or "Choose a target role",
        "days_30": {"focus": "Foundations", "skills": skills[:2], "milestones": milestones[:2]},
        "days_60": {"focus": "Applied practice", "skills": skills[:4], "milestones": milestones[:4]},
        "days_90": {"focus": "Portfolio and review", "skills": skills[:6], "milestones": milestones},
        "learning_topics": learning_topics,
        "portfolio_projects": portfolio_projects,
        "disclaimer": "A rule-based learning outline from detected skill gaps; adjust it to your background and available time.",
    }


def _interview_questions(text: str, target_role: str | None) -> list[dict]:
    analysis = analyze_resume(text, target_role)
    skills = analysis.skills.technical[:4]
    project = next(
        (
            line.strip(" •-\t")
            for line in text.splitlines()
            if not _is_section_heading(line)
            and re.search(r"\b(project|built|developed|implemented|created)\b", line, re.I)
        ),
        "a project or assignment listed on your resume",
    )
    role = _role_name(target_role) or "your target role"
    technical_questions = [
        {
            "type": "Technical",
            "question": f"How have you used {skill} in a practical task, and what trade-offs did you consider?",
            "answer_structure": "Context → approach → technical decision → outcome. Use only a real example.",
            "why": f"Tests whether the resume mention of {skill} is supported by concrete understanding.",
        }
        for skill in skills[:2]
    ]
    if not technical_questions:
        technical_questions.append({
            "type": "Technical",
            "question": "Describe a technical tool or concept you learned and how you applied it.",
            "answer_structure": "Context → what you learned → how you applied it → what you verified.",
            "why": "Use a real example; no technical skills were detected in the supplied resume text.",
        })
    return technical_questions + [
        {
            "type": "Project-based",
            "question": f"Walk me through {project}. What did you personally contribute?",
            "answer_structure": "Situation → your responsibility → actions → verified result → what you learned.",
            "why": "Connects project evidence to individual contribution without assuming unlisted outcomes.",
        },
        {
            "type": "Scenario-based",
            "question": f"How would you approach an unfamiliar {role} problem with incomplete requirements?",
            "answer_structure": "Clarify constraints → break down the problem → evaluate options → communicate risks → validate.",
            "why": "Explores reasoning and communication relevant to the selected role.",
        },
        {
            "type": "HR",
            "question": "Tell me about a challenge you faced while learning or working with a team.",
            "answer_structure": "Situation → specific action you took → outcome you can support → reflection.",
            "why": "Assesses reflection and collaboration using a real experience.",
        },
    ]


def build_intelligence(text: str, target_role: str | None) -> dict:
    analysis = analyze_resume(text, target_role)
    ats = _ats_analysis(text, target_role)
    _, _, missing = _role_coverage(text, target_role)
    return {
        "analysis": analysis.model_dump(),
        "career_dna": _career_dna(text, target_role),
        "ats": ats,
        "readiness": _readiness(text, target_role, ats),
        "roadmap": _roadmap(target_role, missing, analysis.learning_suggestions),
        "interview_questions": _interview_questions(text, target_role),
        "mode": "Rule-based analysis",
    }


def match_job_description(resume: str, description: str) -> dict:
    resume_analysis = analyze_resume(resume)
    resume_skills = {skill.lower(): skill for skill in resume_analysis.skills.technical}
    resume_body = "\n".join(
        line for line in resume.splitlines() if not _is_section_heading(line)
    )
    job_skills = [
        skill for skill in SKILL_CATALOG
        if SKILL_CATALOG[skill][0] == "technical"
        and re.search(rf"(?<!\w){re.escape(skill.lower())}(?!\w)", description.lower())
    ]
    matched = [skill for skill in job_skills if skill.lower() in resume_skills]
    missing = [skill for skill in job_skills if skill.lower() not in resume_skills]
    job_words = {
        word for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", description.lower())
        if word not in {"with", "and", "the", "for", "from", "you", "our", "will", "have", "this", "that", "are", "role", "work"}
    }
    resume_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", resume_body.lower()))
    keyword_overlap = round(len(job_words & resume_words) / len(job_words) * 100) if job_words else 0
    experience_terms = re.findall(r"\b(software|developer|analyst|engineer|intern|project|experience|developed|built|led|managed)\b", description.lower())
    experience_hits = sum(term in resume_body.lower() for term in set(experience_terms))
    experience_score = min(round(experience_hits / max(len(set(experience_terms)), 1) * 100), 100)
    skill_score = round(len(matched) / len(job_skills) * 100) if job_skills else keyword_overlap
    score = round(skill_score * 0.55 + experience_score * 0.25 + keyword_overlap * 0.20)
    suggestions = [f"Add truthful, specific evidence for {skill} if you have used it." for skill in missing[:5]]
    if not suggestions:
        suggestions = ["Make relevant experience and project outcomes easier to scan."]
    described_roles = [
        role for role in ROLE_REQUIREMENTS
        if re.search(rf"(?<!\w){re.escape(role.lower())}(?!\w)", description.lower())
    ]
    if not described_roles:
        described_roles = [item.role for item in analyze_resume(resume).job_recommendations[:3]]
    role_recommendations = []
    for role in described_roles[:3]:
        required = ROLE_REQUIREMENTS[role]
        role_matched = [skill for skill in required if skill.lower() in resume_skills]
        role_missing = [skill for skill in required if skill.lower() not in resume_skills]
        role_recommendations.append({
            "role": role,
            "recommendation": (
                f"Highlight resume evidence for {', '.join(role_matched[:3])}."
                if role_matched
                else f"Add relevant project or coursework evidence for {role} requirements."
            ),
            "missing_skills": role_missing,
        })
    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "relevant_experience": {
            "score": experience_score,
            "evidence": [
                line.strip()
                for line in resume.splitlines()
                if not _is_section_heading(line)
                and re.search(r"\b(project|intern|built|developed|managed)\b", line, re.I)
            ][:5],
        },
        "keyword_compatibility": {"score": keyword_overlap, "matched_terms": sorted(job_words & resume_words)[:25]},
        "role_recommendations": role_recommendations,
        "suggestions": suggestions,
        "calculation": "55% detected technical-skill coverage + 25% role/experience term evidence + 20% job-description word overlap. This is a text comparison heuristic, not a hiring prediction.",
        "mode": "Rule-based comparison",
    }


def rewrite_bullet(bullet: str) -> dict:
    cleaned = re.sub(r"\s+", " ", bullet).strip(" •-\t")
    cleaned = re.sub(r"^(?:i\s+)", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip(".;")
    action_rewrites = {
        "worked on": "Contributed to ",
        "helped with": "Supported ",
        "assisted with": "Supported ",
    }
    action_forward = re.sub(
        r"^(?:worked on|helped with|assisted with)\s+",
        lambda match: action_rewrites[match.group(0).strip().lower()],
        cleaned,
        flags=re.IGNORECASE,
    )
    concise = re.sub(
        r"\b(successfully|really|very|in order to)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    concise = re.sub(r"\s+", " ", concise).strip()
    concise = concise or cleaned
    ats_friendly = re.sub(r"\s+[|/]\s+", " and ", cleaned)
    ats_friendly = re.sub(r"\s*&\s*", " and ", ats_friendly)
    versions = [
        {"style": "Professional", "text": cleaned[0].upper() + cleaned[1:] + "."},
        {"style": "Action-forward", "text": action_forward[0].upper() + action_forward[1:] + "."},
        {"style": "Concise", "text": concise[0].upper() + concise[1:] + "."},
        {"style": "ATS-friendly", "text": ats_friendly[0].upper() + ats_friendly[1:] + "."},
    ]
    unique_versions = []
    for version in versions:
        if version["text"] not in [item["text"] for item in unique_versions]:
            unique_versions.append(version)
    return {
        "versions": unique_versions,
        "metric_prompt": "If accurate, add a measurable result (such as time saved, users served, or error reduction). No metric was invented.",
        "note": "Rewrites retain the supplied claim; verify every statement before using it.",
        "mode": "Rule-based rewrite",
    }


def compare_resumes(first: str, second: str) -> dict:
    first_analysis = analyze_resume(first)
    second_analysis = analyze_resume(second)
    first_ats = _ats_analysis(first)
    second_ats = _ats_analysis(second)
    first_skills = set(first_analysis.skills.technical)
    second_skills = set(second_analysis.skills.technical)
    first_sections = {name for name, pattern in SECTION_PATTERNS.items() if _has_section(first, pattern)}
    second_sections = {name for name, pattern in SECTION_PATTERNS.items() if _has_section(second, pattern)}
    first_lines = {line.strip() for line in first.splitlines() if line.strip()}
    second_lines = {line.strip() for line in second.splitlines() if line.strip()}
    return {
        "first": {
            "ats_score": first_ats["score"],
            "skills": sorted(first_skills),
            "sections": sorted(first_sections),
            "characters": len(first),
        },
        "second": {
            "ats_score": second_ats["score"],
            "skills": sorted(second_skills),
            "sections": sorted(second_sections),
            "characters": len(second),
        },
        "ats_change": second_ats["score"] - first_ats["score"],
        "added_skills": sorted(second_skills - first_skills),
        "removed_skills": sorted(first_skills - second_skills),
        "added_sections": sorted(second_sections - first_sections),
        "removed_sections": sorted(first_sections - second_sections),
        "keyword_improvements": sorted(second_skills - first_skills),
        "added_content": [line[:240] for line in second.splitlines() if line.strip() in second_lines - first_lines][:6],
        "removed_content": [line[:240] for line in first.splitlines() if line.strip() in first_lines - second_lines][:6],
        "summary": "Comparison is based on detected text, catalogued skills, and standard section headings; it does not judge writing quality or verify claims.",
        "mode": "Rule-based comparison",
    }
