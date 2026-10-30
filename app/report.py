from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .schemas import AnalysisResult


def build_analysis_report(analysis: AnalysisResult) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Elevix Resume Analysis",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5545d1"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#17202a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]
    story = [
        Paragraph("Elevix Resume Analysis", title_style),
        Paragraph("Resume summary", heading_style),
        Paragraph(analysis.resume_summary, body_style),
        Paragraph("Skills detected", heading_style),
        Paragraph(
            f"<b>Technical:</b> {', '.join(analysis.skills.technical) or 'None detected'}<br/>"
            f"<b>Soft:</b> {', '.join(analysis.skills.soft) or 'None detected'}<br/>"
            f"<b>Strengths:</b> {', '.join(analysis.skills.strengths) or 'None detected'}",
            body_style,
        ),
        Paragraph("Recommended roles", heading_style),
    ]
    for role in analysis.job_recommendations:
        story.append(
            Paragraph(
                f"<b>{role.role} — {role.suitability_score}%</b><br/>{role.reason}<br/>"
                f"Required skills: {', '.join(role.required_skills)}",
                body_style,
            )
        )
        story.append(Spacer(1, 5))

    story.append(Paragraph("Skill gaps", heading_style))
    for item in analysis.missing_skills:
        story.append(
            Paragraph(
                f"<b>{item.skill} ({item.priority})</b><br/>{item.reason}",
                body_style,
            )
        )
    story.append(Paragraph("Learning roadmap", heading_style))
    for item in analysis.learning_suggestions:
        story.append(
            Paragraph(
                f"<b>{item.topic}</b><br/>{item.project_idea}<br/>"
                f"Resources: {', '.join(item.resources)}",
                body_style,
            )
        )
    story.append(Paragraph("Resume improvements", heading_style))
    for item in analysis.resume_improvements:
        story.append(
            Paragraph(
                f"<b>{item.section}</b><br/>{item.issue}<br/>{item.suggestion}",
                body_style,
            )
        )
    story.append(Spacer(1, 12))
    story.append(Paragraph(analysis.disclaimer, styles["Italic"]))
    document.build(story)
    return output.getvalue()
