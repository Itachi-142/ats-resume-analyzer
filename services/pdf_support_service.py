# services/pdf_report_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Generates a branded PDF report from the ATS analysis result.
# Uses reportlab Platypus for structured layout.
# Returns bytes — callers can send directly or write to file.
# ─────────────────────────────────────────────────────────────────────────────

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Color Palette (matches Streamlit dashboard) ───────────────────────────────
DARK_BG        = colors.HexColor("#0A0E1A")
CARD_BG        = colors.HexColor("#111827")
BORDER         = colors.HexColor("#1E2840")
CYAN           = colors.HexColor("#00D4FF")
GREEN          = colors.HexColor("#00E5A0")
RED            = colors.HexColor("#FF6B6B")
AMBER          = colors.HexColor("#F59E0B")
BLUE           = colors.HexColor("#4F8EF7")
TEXT_PRIMARY   = colors.HexColor("#E8EAF0")
TEXT_SECONDARY = colors.HexColor("#9AA3B8")
TEXT_MUTED     = colors.HexColor("#4A5568")
WHITE          = colors.white

# Recommendation → (text color, background color)
REC_COLORS = {
    "Strong Yes - Advance to Interview":   (colors.HexColor("#00E5A0"), colors.HexColor("#0D2E22")),
    "Yes - Schedule Interview":            (colors.HexColor("#4F8EF7"), colors.HexColor("#0D1A35")),
    "Maybe - Interview with Reservations": (colors.HexColor("#F59E0B"), colors.HexColor("#2E220D")),
    "No - Does Not Meet Requirements":     (colors.HexColor("#FF6B6B"), colors.HexColor("#2E0D0D")),
    "Strong No - Significant Skills Gap":  (colors.HexColor("#FF4444"), colors.HexColor("#2E0505")),
}


# ── Styles ────────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    return {
        "eyebrow": ParagraphStyle("eyebrow",
            fontName="Helvetica", fontSize=7, textColor=CYAN,
            spaceAfter=4, letterSpacing=1.5,
        ),
        "title": ParagraphStyle("title",
            fontName="Helvetica-Bold", fontSize=26, textColor=WHITE,
            spaceAfter=6, leading=30,
        ),
        "subtitle": ParagraphStyle("subtitle",
            fontName="Helvetica", fontSize=10, textColor=TEXT_SECONDARY,
            leading=14,
        ),
        "section_header": ParagraphStyle("section_header",
            fontName="Helvetica-Bold", fontSize=7, textColor=CYAN,
            spaceAfter=8, spaceBefore=16, letterSpacing=1.5,
        ),
        "score_label": ParagraphStyle("score_label",
            fontName="Helvetica", fontSize=7, textColor=TEXT_MUTED,
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "score_cyan":  ParagraphStyle("score_cyan",  fontName="Helvetica-Bold",
            fontSize=22, textColor=CYAN,  alignment=TA_CENTER, leading=26),
        "score_green": ParagraphStyle("score_green", fontName="Helvetica-Bold",
            fontSize=22, textColor=GREEN, alignment=TA_CENTER, leading=26),
        "score_blue":  ParagraphStyle("score_blue",  fontName="Helvetica-Bold",
            fontSize=22, textColor=BLUE,  alignment=TA_CENTER, leading=26),
        "score_amber": ParagraphStyle("score_amber", fontName="Helvetica-Bold",
            fontSize=22, textColor=AMBER, alignment=TA_CENTER, leading=26),
        "card_label": ParagraphStyle("card_label",
            fontName="Helvetica-Bold", fontSize=7, textColor=TEXT_MUTED,
            spaceAfter=6, letterSpacing=1.0,
        ),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=9.5, textColor=TEXT_PRIMARY,
            spaceAfter=6, leading=15,
        ),
        "bullet": ParagraphStyle("bullet",
            fontName="Helvetica", fontSize=9, textColor=TEXT_SECONDARY,
            spaceAfter=5, leading=14, leftIndent=12, firstLineIndent=-12,
        ),
        "skill_matched": ParagraphStyle("skill_matched",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=GREEN, alignment=TA_CENTER,
        ),
        "skill_missing": ParagraphStyle("skill_missing",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=RED, alignment=TA_CENTER,
        ),
    }


# ── Page Template ─────────────────────────────────────────────────────────────

def _on_page(canvas, doc):
    """Draws dark background, top accent bar, and footer on every page."""
    canvas.saveState()

    # Background
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

    # Top accent line
    canvas.setFillColor(CYAN)
    canvas.rect(0, A4[1] - 3, A4[0], 3, fill=1, stroke=0)

    # Footer separator
    canvas.setFillColor(BORDER)
    canvas.rect(20*mm, 12*mm, A4[0] - 40*mm, 0.5, fill=1, stroke=0)

    # Footer text
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        A4[0] / 2, 8*mm,
        f"ATS Resume Analyzer  ·  "
        f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}  ·  "
        f"Powered by Groq LLaMA 3.1"
    )
    canvas.restoreState()


# ── Score Cards ───────────────────────────────────────────────────────────────

def _build_score_cards(scores: dict, styles: dict) -> Table:
    W   = 38*mm
    PAD = 4*mm

    configs = [
        ("OVERALL SCORE", scores["final"],      styles["score_cyan"]),
        ("KEYWORD MATCH", scores["keyword"],    styles["score_green"]),
        ("SEMANTIC MATCH",scores["semantic"],   styles["score_blue"]),
        ("CONFIDENCE",    scores["confidence"], styles["score_amber"]),
    ]
    accents = [CYAN, GREEN, BLUE, AMBER]

    cells = []
    for label, val, vstyle in configs:
        cells.append([
            Paragraph(label, styles["score_label"]),
            Paragraph(f"{int(val * 100)}%", vstyle),
        ])

    t = Table([cells], colWidths=[W + PAD*2]*4, rowHeights=[22*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), CARD_BG),
        *[("BOX",         (i,0), (i,0),   0.5, BORDER)  for i in range(4)],
        *[("LINEABOVE",   (i,0), (i,0),   2, accents[i]) for i in range(4)],
        ("LEFTPADDING",   (0,0), (-1,-1), PAD),
        ("RIGHTPADDING",  (0,0), (-1,-1), PAD),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t


# ── Skills Section ────────────────────────────────────────────────────────────

def _skill_pill_table(skills: list, style, bg_hex: str, border_hex: str) -> Table:
    """Renders skills as pill-tag grid, 3 per row."""
    if not skills:
        return Paragraph("None detected", style)

    bg     = colors.HexColor(bg_hex)
    border = colors.HexColor(border_hex)
    rows, row = [], []

    for i, s in enumerate(skills):
        p    = Paragraph(s, style)
        cell = Table([[p]], colWidths=[22*mm], rowHeights=[6*mm])
        cell.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), bg),
            ("BOX",           (0,0), (-1,-1), 0.5, border),
            ("TOPPADDING",    (0,0), (-1,-1), 1),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ("LEFTPADDING",   (0,0), (-1,-1), 3),
            ("RIGHTPADDING",  (0,0), (-1,-1), 3),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ]))
        row.append(cell)
        if len(row) == 3 or i == len(skills) - 1:
            while len(row) < 3:
                row.append("")
            rows.append(row)
            row = []

    t = Table(rows, colWidths=[23*mm]*3)
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), 2),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
    ]))
    return t


def _build_skills_section(matched: list, missing: list, styles: dict) -> Table:
    PAGE_W = A4[0] - 40*mm
    COL_W  = PAGE_W / 2 - 3*mm

    def make_card(header_text, skills, skill_style, bg_hex, border_hex, accent):
        pills = _skill_pill_table(skills, skill_style, bg_hex, border_hex)
        content = [
            [Paragraph(header_text, styles["card_label"])],
            [pills],
        ]
        t = Table(content, colWidths=[COL_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), CARD_BG),
            ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
            ("LINEABOVE",     (0,0), (0,0),   2, accent),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ]))
        return t

    matched_card = make_card(
        f"MATCHED SKILLS — {len(matched)} FOUND",
        matched, styles["skill_matched"],
        "#0D2E22", "#00E5A030", GREEN,
    )
    missing_card = make_card(
        f"MISSING SKILLS — {len(missing)} GAPS",
        missing, styles["skill_missing"],
        "#2E0D0D", "#FF6B6B30", RED,
    )

    outer = Table([[matched_card, missing_card]], colWidths=[COL_W+3*mm, COL_W+3*mm])
    outer.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 3*mm),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return outer


# ── Feedback Section ──────────────────────────────────────────────────────────

def _build_feedback_section(feedback: dict, styles: dict) -> list:
    PAGE_W = A4[0] - 40*mm
    COL_W  = PAGE_W / 2 - 3*mm
    story  = []

    # Summary card
    summary = Table([
        [Paragraph("RECRUITER SUMMARY", styles["card_label"])],
        [Paragraph(feedback["summary"], styles["body"])],
    ], colWidths=[PAGE_W])
    summary.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), CARD_BG),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("LINEABOVE",     (0,0), (0,0),   2, CYAN),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(summary)
    story.append(Spacer(1, 4*mm))

    # Strengths / Improvements side by side
    def list_card(title, items, icon, accent):
        rows = [[Paragraph(title, styles["card_label"])]]
        for item in items:
            rows.append([Paragraph(f"{icon}  {item}", styles["bullet"])])
        t = Table(rows, colWidths=[COL_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), CARD_BG),
            ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
            ("LINEABOVE",     (0,0), (0,0),   2, accent),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        return t

    two_col = Table([[
        list_card("STRENGTHS",        feedback["strengths"],    "+", GREEN),
        list_card("AREAS TO IMPROVE", feedback["improvements"], "-", RED),
    ]], colWidths=[COL_W+3*mm, COL_W+3*mm])
    two_col.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 3*mm),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(two_col)
    story.append(Spacer(1, 4*mm))

    # Recommendation badge
    rec            = feedback["recommendation"]
    rec_fg, rec_bg = REC_COLORS.get(rec, (AMBER, colors.HexColor("#2E220D")))

    rec_table = Table([
        [Paragraph("HIRING RECOMMENDATION", styles["card_label"])],
        [Paragraph(rec, ParagraphStyle("rec_val",
            fontName="Helvetica-Bold", fontSize=12,
            textColor=rec_fg, alignment=TA_CENTER, leading=16,
        ))],
    ], colWidths=[PAGE_W])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), rec_bg),
        ("BOX",           (0,0), (-1,-1), 1.5, rec_fg),
        ("LINEABOVE",     (0,0), (0,0),   3,   rec_fg),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(rec_table)
    return story


# ── Public Interface ──────────────────────────────────────────────────────────

def generate_pdf_report(result: dict, resume_filename: str = "resume") -> bytes:
    """
    Generate a branded PDF report from the analysis result dict.

    Args:
        result:          The full JSON response from /api/v1/analyze
        resume_filename: Original uploaded filename (shown in report header)

    Returns:
        PDF as raw bytes — pass directly to Streamlit's st.download_button
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=20*mm,
    )

    styles = _build_styles()
    story  = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("AI-POWERED EVALUATION SYSTEM", styles["eyebrow"]))
    story.append(Paragraph("ATS Resume Analysis Report", styles["title"]))
    story.append(Paragraph(
        f"Resume: <b>{resume_filename}</b>  &nbsp;·&nbsp;  "
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4*mm))

    # ── Scores ────────────────────────────────────────────────────────────────
    story.append(Paragraph("ANALYSIS SCORES", styles["section_header"]))
    story.append(_build_score_cards(result["scores"], styles))
    story.append(Spacer(1, 4*mm))

    # ── Skills ────────────────────────────────────────────────────────────────
    story.append(Paragraph("SKILL ANALYSIS", styles["section_header"]))
    story.append(_build_skills_section(
        result["matched_skills"],
        result["missing_skills"],
        styles,
    ))
    story.append(Spacer(1, 4*mm))

    # ── Feedback ──────────────────────────────────────────────────────────────
    story.append(Paragraph("RECRUITER FEEDBACK", styles["section_header"]))
    story.extend(_build_feedback_section(result["feedback"], styles))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buffer.seek(0)
    return buffer.read()

def generate_batch_pdf_report(batch_result: dict) -> bytes:
    """
    Generate a ranked batch PDF report for multiple candidates.
    """
    from reportlab.platypus import PageBreak

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=20*mm,
    )

    styles    = _build_styles()
    story     = []
    medals    = {1: "1st", 2: "2nd", 3: "3rd"}
    candidates = batch_result["candidates"]
    total      = batch_result["total_candidates"]

    # ── Cover Header ──────────────────────────────────────────────────────────
    story.append(Paragraph("AI-POWERED EVALUATION SYSTEM", styles["eyebrow"]))
    story.append(Paragraph("Batch Candidate Ranking Report", styles["title"]))
    story.append(Paragraph(
        f"Total Candidates: <b>{total}</b>  &nbsp;·&nbsp;  "
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4*mm))

    # ── Summary Ranking Table ─────────────────────────────────────────────────
    story.append(Paragraph("CANDIDATE RANKINGS", styles["section_header"]))

    PAGE_W   = A4[0] - 40*mm
    col_widths = [15*mm, 45*mm, 22*mm, 22*mm, 22*mm, 44*mm]

    table_data = [[
        Paragraph("RANK",     styles["score_label"]),
        Paragraph("CANDIDATE",styles["score_label"]),
        Paragraph("OVERALL",  styles["score_label"]),
        Paragraph("KEYWORD",  styles["score_label"]),
        Paragraph("SEMANTIC", styles["score_label"]),
        Paragraph("VERDICT",  styles["score_label"]),
    ]]

    rec_fg_map = {
        "Strong Yes - Advance to Interview":   colors.HexColor("#00E5A0"),
        "Yes - Schedule Interview":            colors.HexColor("#4F8EF7"),
        "Maybe - Interview with Reservations": colors.HexColor("#F59E0B"),
        "No - Does Not Meet Requirements":     colors.HexColor("#FF6B6B"),
        "Strong No - Significant Skills Gap":  colors.HexColor("#FF4444"),
    }

    for c in candidates:
        rank    = c["rank"]
        medal   = {1:"🥇", 2:"🥈", 3:"🥉"}.get(rank, f"#{rank}")
        score   = int(c["scores"]["final"]    * 100)
        keyword = int(c["scores"]["keyword"]  * 100)
        sem     = int(c["scores"]["semantic"] * 100)
        rec     = c["feedback"]["recommendation"]
        fg      = rec_fg_map.get(rec, colors.HexColor("#F59E0B"))
        name    = c["filename"].rsplit(".", 1)[0][:28]

        table_data.append([
            Paragraph(f"{medal}", styles["body"]),
            Paragraph(name,       styles["body"]),
            Paragraph(f"{score}%",  ParagraphStyle("sv", fontName="Helvetica-Bold",
                fontSize=11, textColor=CYAN, alignment=TA_CENTER)),
            Paragraph(f"{keyword}%", ParagraphStyle("kv", fontName="Helvetica-Bold",
                fontSize=10, textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(f"{sem}%",    ParagraphStyle("semv", fontName="Helvetica-Bold",
                fontSize=10, textColor=BLUE, alignment=TA_CENTER)),
            Paragraph(rec, ParagraphStyle("rv", fontName="Helvetica-Bold",
                fontSize=7, textColor=fg, alignment=TA_CENTER)),
        ])

    ranking_table = Table(table_data, colWidths=col_widths)
    ranking_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#0D1421")),
        ("BACKGROUND",    (0,1), (-1,-1), CARD_BG),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("LINEABOVE",     (0,0), (-1,0),  2, CYAN),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (2,0), (-1,-1), "CENTER"),
    ]))
    story.append(ranking_table)

    # ── Individual Reports ────────────────────────────────────────────────────
    for c in candidates:
        story.append(PageBreak())

        rank = c["rank"]
        medal = {1:"🥇", 2:"🥈", 3:"🥉"}.get(rank, f"Rank #{rank}")

        story.append(Paragraph("CANDIDATE DETAIL REPORT", styles["eyebrow"]))
        story.append(Paragraph(
            f"{medal}  Rank #{rank} — {c['filename']}",
            styles["title"],
        ))
        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("ANALYSIS SCORES", styles["section_header"]))
        story.append(_build_score_cards(c["scores"], styles))
        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("SKILL ANALYSIS", styles["section_header"]))
        story.append(_build_skills_section(
            c["matched_skills"], c["missing_skills"], styles
        ))
        story.append(Spacer(1, 4*mm))

        story.append(Paragraph("RECRUITER FEEDBACK", styles["section_header"]))
        story.extend(_build_feedback_section(c["feedback"], styles))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buffer.seek(0)
    return buffer.read()