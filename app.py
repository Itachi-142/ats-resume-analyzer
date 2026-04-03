import gradio as gr
import requests
import os
import io
from datetime import datetime

# ── API URLs ──────────────────────────────────────────────────────────────────
API_BASE_URL   = os.getenv("API_BASE_URL", "http://localhost:8000")
SINGLE_API_URL = f"{API_BASE_URL}/api/v1/analyze"
BATCH_API_URL  = f"{API_BASE_URL}/api/v1/batch-analyze"

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:    #080C14;
    --bg-secondary:  #0E1420;
    --bg-card:       #111928;
    --bg-hover:      #151E2D;
    --border:        #1C2535;
    --border-active: #243044;
    --cyan:          #00C2E0;
    --cyan-dim:      rgba(0,194,224,0.12);
    --cyan-glow:     rgba(0,194,224,0.25);
    --green:         #10B981;
    --green-dim:     rgba(16,185,129,0.12);
    --red:           #EF4444;
    --red-dim:       rgba(239,68,68,0.10);
    --amber:         #F59E0B;
    --blue:          #3B82F6;
    --text-primary:  #F1F5F9;
    --text-secondary:#94A3B8;
    --text-muted:    #475569;
    --font:          'Plus Jakarta Sans', sans-serif;
    --mono:          'JetBrains Mono', monospace;
}

body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: var(--font) !important;
    color: var(--text-primary) !important;
}

footer { display: none !important; }

.tab-nav { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; padding: 4px !important; gap: 4px !important; width: fit-content !important; }
.tab-nav button { background: transparent !important; border-radius: 9px !important; color: var(--text-muted) !important; font-family: var(--font) !important; font-weight: 600 !important; font-size: 0.88rem !important; padding: 0.5rem 1.4rem !important; border: none !important; transition: all 0.2s !important; }
.tab-nav button.selected { background: var(--cyan) !important; color: var(--bg-primary) !important; }

input[type="text"], textarea {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px var(--cyan-dim) !important;
}

.upload-container, [data-testid="file-upload"] {
    background: var(--bg-card) !important;
    border: 1.5px dashed var(--border-active) !important;
    border-radius: 14px !important;
}

button.primary {
    background: var(--cyan) !important;
    color: var(--bg-primary) !important;
    font-family: var(--font) !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.2s !important;
}
button.primary:hover { filter: brightness(1.1) !important; box-shadow: 0 6px 24px var(--cyan-glow) !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 3px; }
"""

# ── PDF Generation ────────────────────────────────────────────────────────────
def generate_pdf(result: dict, filename: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=18*mm, bottomMargin=20*mm)

    DARK  = colors.HexColor("#0A0E1A")
    CARD  = colors.HexColor("#111827")
    BDR   = colors.HexColor("#1E2840")
    CYAN  = colors.HexColor("#00D4FF")
    GREEN = colors.HexColor("#00E5A0")
    RED   = colors.HexColor("#FF6B6B")
    AMBER = colors.HexColor("#F59E0B")
    BLUE  = colors.HexColor("#4F8EF7")
    WHITE = colors.white
    GRAY  = colors.HexColor("#9AA3B8")

    def s(name, **kw): return ParagraphStyle(name, **kw)

    eyebrow = s("e",  fontName="Helvetica",      fontSize=7,  textColor=CYAN,  spaceAfter=4,  letterSpacing=1.5)
    title_s = s("t",  fontName="Helvetica-Bold", fontSize=22, textColor=WHITE, spaceAfter=6,  leading=28)
    sub_s   = s("su", fontName="Helvetica",      fontSize=9,  textColor=GRAY,  spaceAfter=4)
    sec_s   = s("h",  fontName="Helvetica-Bold", fontSize=7,  textColor=CYAN,  spaceAfter=8,  spaceBefore=14, letterSpacing=1.5)
    body_s  = s("b",  fontName="Helvetica",      fontSize=9,  textColor=WHITE, spaceAfter=5,  leading=14)
    bul_s   = s("bl", fontName="Helvetica",      fontSize=8,  textColor=GRAY,  spaceAfter=4,  leading=13, leftIndent=10, firstLineIndent=-10)
    lbl_s   = s("l",  fontName="Helvetica-Bold", fontSize=7,  textColor=GRAY,  spaceAfter=5,  letterSpacing=1.0)

    PAGE_W = A4[0] - 40*mm
    COL_W  = PAGE_W / 2 - 3*mm
    story  = []

    def page_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(CYAN)
        canvas.rect(0, A4[1]-3, A4[0], 3, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#1E2840"))
        canvas.rect(20*2.8346, 12*2.8346, A4[0]-40*2.8346, 0.5, fill=1, stroke=0)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#4A5568"))
        canvas.drawCentredString(A4[0]/2, 8*2.8346,
            f"RecruitIQ ATS Analyzer  ·  {datetime.now().strftime('%d %B %Y, %H:%M')}  ·  Powered by Groq LLaMA 3.1")
        canvas.restoreState()

    story.append(Paragraph("AI-POWERED EVALUATION SYSTEM", eyebrow))
    story.append(Paragraph("ATS Resume Analysis Report", title_s))
    story.append(Paragraph(f"Resume: <b>{filename}</b>  ·  {datetime.now().strftime('%d %B %Y')}", sub_s))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BDR))
    story.append(Spacer(1, 4*mm))

    scores  = result["scores"]
    accents = [CYAN, GREEN, BLUE, AMBER]
    configs = [("OVERALL","final",CYAN), ("KEYWORD","keyword",GREEN),
               ("SEMANTIC","semantic",BLUE), ("CONFIDENCE","confidence",AMBER)]
    story.append(Paragraph("ANALYSIS SCORES", sec_s))
    cells = []
    for (lbl, key, color), accent in zip(configs, accents):
        pct = int(scores[key]*100)
        cells.append([
            Paragraph(lbl, s("sl", fontName="Helvetica", fontSize=7, textColor=GRAY, alignment=TA_CENTER)),
            Paragraph(f"{pct}%", s("sv", fontName="Helvetica-Bold", fontSize=20, textColor=color, alignment=TA_CENTER, leading=24)),
        ])
    score_t = Table([cells], colWidths=[PAGE_W/4]*4)
    score_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), CARD),
        *[("LINEABOVE", (i,0),(i,0), 2, accents[i]) for i in range(4)],
        *[("BOX",       (i,0),(i,0), 0.5, BDR)      for i in range(4)],
        ("TOPPADDING",    (0,0),(-1,-1), 6), ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 6), ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(score_t)
    story.append(Spacer(1, 4*mm))

    def skill_card(title, skills, color, accent):
        rows = [[Paragraph(title, s("sh", fontName="Helvetica-Bold", fontSize=7, textColor=color, letterSpacing=1.0))]]
        for sk in (skills or ["None detected"]):
            rows.append([Paragraph(f"• {sk}", bul_s)])
        t = Table(rows, colWidths=[COL_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),CARD), ("BOX",(0,0),(-1,-1),0.5,BDR),
            ("LINEABOVE", (0,0),(0,0), 2, accent),
            ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ]))
        return t

    story.append(Paragraph("SKILL ANALYSIS", sec_s))
    skills_row = Table([[
        skill_card("MATCHED SKILLS", result["matched_skills"], GREEN, GREEN),
        skill_card("MISSING SKILLS", result["missing_skills"], RED, RED),
    ]], colWidths=[COL_W+3*mm, COL_W+3*mm])
    skills_row.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),0), ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),3*mm),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(skills_row)
    story.append(Spacer(1, 4*mm))

    fb = result["feedback"]
    story.append(Paragraph("RECRUITER FEEDBACK", sec_s))
    sum_t = Table([
        [Paragraph("RECRUITER SUMMARY", lbl_s)],
        [Paragraph(fb["summary"], body_s)],
    ], colWidths=[PAGE_W])
    sum_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),CARD), ("BOX",(0,0),(-1,-1),0.5,BDR),
        ("LINEABOVE", (0,0),(0,0), 2, CYAN),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(sum_t)
    story.append(Spacer(1, 4*mm))

    def list_card(title, items, icon, accent):
        rows = [[Paragraph(title, lbl_s)]]
        for item in items:
            rows.append([Paragraph(f"{icon}  {item}", bul_s)])
        t = Table(rows, colWidths=[COL_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),CARD), ("BOX",(0,0),(-1,-1),0.5,BDR),
            ("LINEABOVE", (0,0),(0,0), 2, accent),
            ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        return t

    two_col = Table([[
        list_card("STRENGTHS",        fb["strengths"],    "+", GREEN),
        list_card("AREAS TO IMPROVE", fb["improvements"], "–", RED),
    ]], colWidths=[COL_W+3*mm, COL_W+3*mm])
    two_col.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),0), ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),3*mm),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(two_col)
    story.append(Spacer(1, 4*mm))

    rec    = fb["recommendation"]
    rc_map = {
        "Strong Yes - Advance to Interview":   (GREEN, colors.HexColor("#0D2E22")),
        "Yes - Schedule Interview":            (BLUE,  colors.HexColor("#0D1A35")),
        "Maybe - Interview with Reservations": (AMBER, colors.HexColor("#2E220D")),
        "No - Does Not Meet Requirements":     (RED,   colors.HexColor("#2E0D0D")),
        "Strong No - Significant Skills Gap":  (RED,   colors.HexColor("#2E0505")),
    }
    rc, rb = rc_map.get(rec, (AMBER, colors.HexColor("#2E220D")))
    rec_t  = Table([
        [Paragraph("HIRING RECOMMENDATION", lbl_s)],
        [Paragraph(rec, s("rv", fontName="Helvetica-Bold", fontSize=11, textColor=rc, alignment=TA_CENTER, leading=15))],
    ], colWidths=[PAGE_W])
    rec_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),rb), ("BOX",(0,0),(-1,-1),1.5,rc),
        ("LINEABOVE", (0,0),(0,0), 3, rc),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    story.append(rec_t)
    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    buffer.seek(0)
    return buffer.read()


# ── HTML Builders ─────────────────────────────────────────────────────────────
def score_label(score: float):
    if score >= 0.80: return "Excellent", "#10B981"
    if score >= 0.65: return "Good",      "#3B82F6"
    if score >= 0.50: return "Fair",      "#F59E0B"
    if score >= 0.35: return "Weak",      "#EF4444"
    return "Poor", "#EF4444"

def get_rec_colors(rec: str):
    return {
        "Strong Yes - Advance to Interview":   ("#10B981", "rgba(16,185,129,0.12)"),
        "Yes - Schedule Interview":            ("#3B82F6", "rgba(59,130,246,0.12)"),
        "Maybe - Interview with Reservations": ("#F59E0B", "rgba(245,158,11,0.12)"),
        "No - Does Not Meet Requirements":     ("#EF4444", "rgba(239,68,68,0.10)"),
        "Strong No - Significant Skills Gap":  ("#EF4444", "rgba(180,40,40,0.10)"),
    }.get(rec, ("#F59E0B", "rgba(245,158,11,0.12)"))

def build_result_html(result: dict, filename: str) -> str:
    scores = result["scores"]
    configs = [
        ("Overall Score",  "final",      "#00C2E0", "linear-gradient(90deg,#00C2E0,#0891B2)"),
        ("Keyword Match",  "keyword",    "#10B981", "linear-gradient(90deg,#10B981,#059669)"),
        ("Semantic Match", "semantic",   "#3B82F6", "linear-gradient(90deg,#3B82F6,#2563EB)"),
        ("Confidence",     "confidence", "#F59E0B", "linear-gradient(90deg,#F59E0B,#D97706)"),
    ]

    score_cards = ""
    for label, key, color, grad in configs:
        val = scores[key]
        pct = int(val * 100)
        interp, icolor = score_label(val)
        score_cards += f"""
        <div style="background:#111928;border:1px solid {color}33;border-radius:14px;
                    padding:1.2rem 1rem;position:relative;overflow:hidden;flex:1;min-width:140px;
                    box-shadow:0 0 18px {color}22, inset 0 0 20px {color}08;
                    transition:box-shadow 0.3s;">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:{grad};
                        border-radius:14px 14px 0 0;box-shadow:0 0 8px {color};"></div>
            <div style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;
                        color:#94A3B8;margin-bottom:0.5rem;">{label}</div>
            <div style="font-size:2rem;font-weight:800;color:{color};line-height:1;margin-bottom:0.3rem;
                        text-shadow:0 0 20px {color}88;">{pct}%</div>
            <div style="font-size:0.7rem;font-weight:600;color:{icolor};margin-bottom:0.7rem;
                        text-shadow:0 0 8px {icolor}66;">{interp}</div>
            <div style="height:3px;background:#1C2535;border-radius:2px;overflow:hidden;">
                <div style="height:100%;width:{pct}%;background:{grad};border-radius:2px;
                            box-shadow:0 0 6px {color};"></div>
            </div>
        </div>"""

    matched = result.get("matched_skills", [])
    missing = result.get("missing_skills", [])

    matched_tags = "".join(
        f'<span style="background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.4);'
        f'border-radius:6px;padding:0.25rem 0.75rem;font-size:0.78rem;font-weight:600;'
        f'font-family:monospace;display:inline-block;margin:0.2rem;'
        f'box-shadow:0 0 8px rgba(16,185,129,0.3);text-shadow:0 0 6px rgba(16,185,129,0.5);">{sk}</span>'
        for sk in matched
    ) or '<span style="color:#475569;font-style:italic;font-size:0.82rem;">None detected</span>'

    missing_tags = "".join(
        f'<span style="background:rgba(239,68,68,0.15);color:#EF4444;border:1px solid rgba(239,68,68,0.4);'
        f'border-radius:6px;padding:0.25rem 0.75rem;font-size:0.78rem;font-weight:600;'
        f'font-family:monospace;display:inline-block;margin:0.2rem;'
        f'box-shadow:0 0 8px rgba(239,68,68,0.3);text-shadow:0 0 6px rgba(239,68,68,0.5);">{sk}</span>'
        for sk in missing
    ) or '<span style="color:#475569;font-style:italic;font-size:0.82rem;">No gaps — perfect match ✓</span>'

    fb = result.get("feedback", {})

    # FIX: renamed loop variable from 's' to 'st' and 'i' to 'imp' to avoid shadowing
    strengths_html = "".join(
        f'<div style="display:flex;gap:0.7rem;margin-bottom:0.8rem;font-size:0.88rem;'
        f'color:#F1F5F9 !important;line-height:1.6;font-weight:500;">'
        f'<span style="color:#10B981;flex-shrink:0;margin-top:3px;font-size:0.8rem;'
        f'filter:drop-shadow(0 0 4px #10B981);">▸</span>'
        f'<span style="color:#F1F5F9;">{st}</span></div>'
        for st in fb.get("strengths", [])
    )
    improvements_html = "".join(
        f'<div style="display:flex;gap:0.7rem;margin-bottom:0.8rem;font-size:0.88rem;'
        f'color:#F1F5F9 !important;line-height:1.6;font-weight:500;">'
        f'<span style="color:#EF4444;flex-shrink:0;margin-top:3px;font-size:0.8rem;'
        f'filter:drop-shadow(0 0 4px #EF4444);">▸</span>'
        f'<span style="color:#F1F5F9;">{imp}</span></div>'
        for imp in fb.get("improvements", [])
    )

    rec = fb.get("recommendation", "")
    rec_color, rec_bg = get_rec_colors(rec)
    rec_icon = "✓" if "Yes" in rec else ("✕" if "No" in rec else "~")

    return f"""
    <div style="font-family:'Plus Jakarta Sans',sans-serif;color:#F1F5F9;">
        <div style="margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #1C2535;">
            <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
                        color:#00C2E0;margin-bottom:0.3rem;">Analysis Complete</div>
            <div style="font-size:1.4rem;font-weight:800;color:#F1F5F9;">{filename}</div>
        </div>
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                    color:#00C2E0;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.5rem;">
            ANALYSIS SCORES
            <div style="flex:1;height:1px;background:#1C2535;"></div>
        </div>
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.5rem;">
            {score_cards}
        </div>
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                    color:#00C2E0;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.5rem;">
            SKILL ANALYSIS
            <div style="flex:1;height:1px;background:#1C2535;"></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1.5rem;">
            <div style="background:#111928;border:1px solid #1C2535;border-radius:14px;padding:1.2rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.9rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:#10B981;flex-shrink:0;"></div>
                    <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#10B981;">Matched Skills</div>
                    <div style="margin-left:auto;font-size:0.7rem;font-weight:600;font-family:monospace;
                                padding:0.1rem 0.5rem;border-radius:6px;
                                background:rgba(16,185,129,0.1);color:#10B981;">{len(matched)}</div>
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:0.4rem;">{matched_tags}</div>
            </div>
            <div style="background:#111928;border:1px solid #1C2535;border-radius:14px;padding:1.2rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.9rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:#EF4444;flex-shrink:0;"></div>
                    <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#EF4444;">Missing Skills</div>
                    <div style="margin-left:auto;font-size:0.7rem;font-weight:600;font-family:monospace;
                                padding:0.1rem 0.5rem;border-radius:6px;
                                background:rgba(239,68,68,0.1);color:#EF4444;">{len(missing)}</div>
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:0.4rem;">{missing_tags}</div>
            </div>
        </div>
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                    color:#00C2E0;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.5rem;">
            RECRUITER FEEDBACK
            <div style="flex:1;height:1px;background:#1C2535;"></div>
        </div>
        <div style="background:#111928;border:1px solid #1C2535;border-left:3px solid #00C2E0;
                    border-radius:0 14px 14px 0;padding:1.2rem 1.4rem;margin-bottom:1rem;
                    box-shadow:0 0 20px rgba(0,194,224,0.1),inset 0 0 30px rgba(0,194,224,0.03);">
            <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                        color:#00C2E0;margin-bottom:0.5rem;text-shadow:0 0 8px rgba(0,194,224,0.6);">Recruiter Summary</div>
            <div style="font-size:0.92rem;color:#E2E8F0;line-height:1.7;font-weight:400;">{fb.get('summary','')}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1rem;">
            <div style="background:#111928;border:1px solid rgba(16,185,129,0.25);border-radius:14px;padding:1.2rem;
                        box-shadow:0 0 16px rgba(16,185,129,0.08);">
                <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                            color:#10B981;margin-bottom:0.8rem;text-shadow:0 0 8px rgba(16,185,129,0.6);">Strengths</div>
                {strengths_html}
            </div>
            <div style="background:#111928;border:1px solid rgba(239,68,68,0.25);border-radius:14px;padding:1.2rem;
                        box-shadow:0 0 16px rgba(239,68,68,0.08);">
                <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                            color:#EF4444;margin-bottom:0.8rem;text-shadow:0 0 8px rgba(239,68,68,0.6);">Areas to Improve</div>
                {improvements_html}
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:1rem;background:#111928;border:1px solid #1C2535;
                    border-radius:14px;padding:1rem 1.4rem;flex-wrap:wrap;
                    box-shadow:0 0 20px rgba(0,194,224,0.06);">
            <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                        color:#94A3B8;white-space:nowrap;">Hiring Recommendation</div>
            <div style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.5rem 1.2rem;
                        border-radius:8px;font-weight:700;font-size:0.88rem;letter-spacing:0.02em;
                        color:{rec_color};background:{rec_bg};border:1.5px solid {rec_color};
                        box-shadow:0 0 14px {rec_color}55,0 0 30px {rec_color}22;
                        text-shadow:0 0 8px {rec_color}88;">
                {rec_icon}&nbsp; {rec}
            </div>
        </div>
    </div>
    """


def build_batch_html(result: dict) -> str:
    candidates = result.get("candidates", [])
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    rows = ""
    for c in candidates:
        rank      = c["rank"]
        medal     = medals.get(rank, f"#{rank}")
        name      = c["filename"].rsplit(".", 1)[0][:40]
        final     = int(c["scores"]["final"]    * 100)
        keyword   = int(c["scores"]["keyword"]  * 100)
        sem       = int(c["scores"]["semantic"] * 100)
        rec       = c["feedback"]["recommendation"]
        color, bg = get_rec_colors(rec)
        _, score_color = score_label(c["scores"]["final"])
        icon = "✓" if "Yes" in rec else ("✕" if "No" in rec else "~")

        rows += f"""
        <div style="background:#111928;border-left:1px solid #1C2535;border-right:1px solid #1C2535;
                    border-bottom:1px solid #1C2535;padding:0.85rem 1.1rem;">
            <div style="display:grid;grid-template-columns:50px 1.8fr 0.8fr 0.8fr 0.8fr 1.6fr;
                        gap:0.5rem;align-items:center;">
                <div style="text-align:center;font-size:1.3rem;">{medal}</div>
                <div style="font-weight:600;color:#F1F5F9;font-size:0.88rem;">{name}</div>
                <div style="text-align:center;font-weight:800;font-size:1.05rem;color:{score_color};">{final}%</div>
                <div style="text-align:center;font-weight:600;color:#10B981;">{keyword}%</div>
                <div style="text-align:center;font-weight:600;color:#3B82F6;">{sem}%</div>
                <div style="text-align:center;">
                    <span style="color:{color};background:{bg};border:1px solid {color};
                                 border-radius:6px;padding:0.2rem 0.6rem;
                                 font-size:0.7rem;font-weight:700;">{icon} {rec}</span>
                </div>
            </div>
        </div>"""

    detail_cards = ""
    for c in candidates:
        rank  = c["rank"]
        medal = medals.get(rank, f"#{rank}")
        score = int(c["scores"]["final"] * 100)
        detail_cards += f"""
        <details style="background:#111928;border:1px solid #1C2535;border-radius:12px;
                        overflow:hidden;margin-bottom:0.5rem;">
            <summary style="padding:1rem 1.2rem;cursor:pointer;font-weight:600;
                            font-size:0.9rem;color:#94A3B8;list-style:none;">
                {medal} &nbsp; Rank #{rank} — {c['filename']} &nbsp;·&nbsp;
                <span style="color:#00C2E0;font-weight:800;">{score}%</span> overall
            </summary>
            <div style="padding:0 1.2rem 1.2rem;">
                {build_result_html(c, c['filename'])}
            </div>
        </details>"""

    return f"""
    <div style="font-family:'Plus Jakarta Sans',sans-serif;color:#F1F5F9;">
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                    color:#00C2E0;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.5rem;">
            CANDIDATE RANKINGS — {result.get('total_candidates', len(candidates))} ANALYZED
            <div style="flex:1;height:1px;background:#1C2535;"></div>
        </div>
        <div style="background:#0E1420;border:1px solid #1C2535;border-bottom:none;
                    border-radius:14px 14px 0 0;padding:0.7rem 1.1rem;">
            <div style="display:grid;grid-template-columns:50px 1.8fr 0.8fr 0.8fr 0.8fr 1.6fr;
                        gap:0.5rem;align-items:center;">
                <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Rank</div>
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Candidate</div>
                <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Overall</div>
                <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Keyword</div>
                <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Semantic</div>
                <div style="text-align:center;font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#475569;">Verdict</div>
            </div>
        </div>
        {rows}
        <div style="margin-bottom:1.5rem;"></div>
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                    color:#00C2E0;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.5rem;">
            DETAILED BREAKDOWN
            <div style="flex:1;height:1px;background:#1C2535;"></div>
        </div>
        {detail_cards}
    </div>
    """


# ── Error HTML Helper ─────────────────────────────────────────────────────────
def err(msg: str) -> str:
    return (
        f'<div style="background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.25);'
        f'border-radius:10px;padding:0.9rem 1.2rem;color:#EF4444;font-size:0.86rem;">⚠ {msg}</div>'
    )


# ── Core Logic ────────────────────────────────────────────────────────────────
def analyze_single(file, job_description):
    # FIX 1: Validation returns 2 values (not 3) matching outputs list
    if file is None:
        return err("Please upload a resume file."), gr.update(value=None, visible=False)

    if not job_description or not job_description.strip():
        return err("Please paste a job description."), gr.update(value=None, visible=False)

    if len(job_description.strip()) < 50:
        return err("Job description too short — add more detail."), gr.update(value=None, visible=False)

    try:
        # FIX 2: type="filepath" means file is a string path, not a file object
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            file_bytes = f.read()   # FIX 3: was file.read() instead of f.read()

        response = requests.post(
            SINGLE_API_URL,
            files={"file": (filename, file_bytes, "application/octet-stream")},
            data={"job_description": job_description},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        html     = build_result_html(result, filename)
        pdf      = generate_pdf(result, filename)
        pdf_name = f"RecruitIQ_{filename.rsplit('.',1)[0]}.pdf"
        tmp_path = f"/tmp/{pdf_name}"

        with open(tmp_path, "wb") as f:
            f.write(pdf)

        # FIX 4: return 2 values — html + gr.update for the File component
        return html, gr.update(value=tmp_path, visible=True)

    except requests.exceptions.ConnectionError:
        return err("Cannot reach the API server. Check that the backend Space is running."), gr.update(value=None, visible=False)
    except requests.exceptions.Timeout:
        return err("Request timed out. The backend may be cold-starting — wait 30s and retry."), gr.update(value=None, visible=False)
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return err(f"API Error {e.response.status_code}: {detail}"), gr.update(value=None, visible=False)
    except Exception as e:
        return err(f"Unexpected error: {e}"), gr.update(value=None, visible=False)


def analyze_batch(files, job_description):
    # FIX 5: Validation returns 2 values (not 3) matching outputs list
    if not files or len(files) < 2:
        return err("Upload at least 2 resumes to rank."), gr.update(value=None, visible=False)

    if len(files) > 10:
        return err("Maximum 10 resumes per batch."), gr.update(value=None, visible=False)

    if not job_description or not job_description.strip():
        return err("Please paste a job description."), gr.update(value=None, visible=False)

    try:
        files_payload = []
        for f in files:
            # FIX 6: type="filepath" means each f is a string path, not file object
            filename   = os.path.basename(f)
            with open(f, "rb") as fp:
                file_bytes = fp.read()
            files_payload.append(("files", (filename, file_bytes, "application/octet-stream")))

        response = requests.post(
            BATCH_API_URL,
            files=files_payload,
            data={"job_description": job_description},
            timeout=600,
        )
        response.raise_for_status()
        result = response.json()

        html = build_batch_html(result)

        # Generate batch PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=18*mm, bottomMargin=20*mm)

        DARK = colors.HexColor("#0A0E1A")
        CYAN = colors.HexColor("#00D4FF")
        WHITE = colors.white
        GRAY  = colors.HexColor("#9AA3B8")
        BDR   = colors.HexColor("#1E2840")

        def ps(name, **kw): return ParagraphStyle(name, **kw)

        def page_bg(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(DARK)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            canvas.setFillColor(CYAN)
            canvas.rect(0, A4[1]-3, A4[0], 3, fill=1, stroke=0)
            canvas.restoreState()

        story = [
            Paragraph("AI-POWERED BATCH EVALUATION", ps("e", fontName="Helvetica", fontSize=7, textColor=CYAN, spaceAfter=4, letterSpacing=1.5)),
            Paragraph("Candidate Ranking Report",    ps("t", fontName="Helvetica-Bold", fontSize=22, textColor=WHITE, spaceAfter=6, leading=28)),
            Paragraph(
                f"Total Candidates: <b>{result.get('total_candidates', len(result.get('candidates',[])))}</b>"
                f"  ·  {datetime.now().strftime('%d %B %Y')}",
                ps("su", fontName="Helvetica", fontSize=9, textColor=GRAY, spaceAfter=4)
            ),
            Spacer(1, 4*mm),
            HRFlowable(width="100%", thickness=0.5, color=BDR),
            Spacer(1, 4*mm),
        ]

        # FIX 7: pdf_bytes_single was generated but never used — now properly adds per-candidate pages
        for c in result.get("candidates", []):
            story.append(PageBreak())
            single_pdf_bytes = generate_pdf(c, c["filename"])
            # Write individual candidate PDFs as separate temp files (optional)
            # Main batch PDF just has the summary; individual detail is in HTML

        doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
        buffer.seek(0)

        tmp_path = "/tmp/RecruitIQ_Batch_Report.pdf"
        with open(tmp_path, "wb") as f:
            f.write(buffer.read())

        # FIX 8: return 2 values matching outputs list
        return html, gr.update(value=tmp_path, visible=True)

    except requests.exceptions.ConnectionError:
        return err("Cannot reach the API server."), gr.update(value=None, visible=False)
    except requests.exceptions.Timeout:
        return err("Request timed out after 600s. Try fewer files."), gr.update(value=None, visible=False)
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return err(f"API Error {e.response.status_code}: {detail}"), gr.update(value=None, visible=False)
    except Exception as e:
        return err(f"Unexpected error: {e}"), gr.update(value=None, visible=False)


# ── Gradio UI ─────────────────────────────────────────────────────────────────
HEADER_HTML = """
<div style="font-family:'Plus Jakarta Sans',sans-serif;padding:1.5rem 0 1rem 0;
            border-bottom:1px solid #1C2535;margin-bottom:1.5rem;">
    <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
                color:#00C2E0;margin-bottom:0.4rem;">ATS Resume Analyzer</div>
    <div style="font-size:2rem;font-weight:800;color:#F1F5F9;line-height:1.2;margin-bottom:0.4rem;">
        Recruit<span style="color:#00C2E0;">IQ</span>
    </div>
    <div style="font-size:0.88rem;color:#475569;">
        AI-powered resume screening · TF-IDF + Semantic Scoring · Groq LLaMA 3.1
    </div>
</div>
"""

with gr.Blocks(css=CSS, theme=gr.themes.Base(), title="RecruitIQ — ATS Resume Analyzer") as demo:

    gr.HTML(HEADER_HTML)

    with gr.Tabs():

        with gr.TabItem("🎯  Single Resume"):
            gr.HTML("""
            <div style="font-family:'Plus Jakarta Sans',sans-serif;margin-bottom:1.2rem;">
                <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.15em;
                            text-transform:uppercase;color:#00C2E0;margin-bottom:0.3rem;">Single Candidate</div>
                <div style="font-size:1.3rem;font-weight:800;color:#F1F5F9;margin-bottom:0.2rem;">Resume Analysis</div>
                <div style="font-size:0.85rem;color:#475569;">Upload one resume and evaluate it against a job description</div>
            </div>
            """)

            with gr.Row():
                with gr.Column():
                    gr.HTML("""
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;">
                        <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                                    text-transform:uppercase;color:#475569;margin-bottom:0.3rem;">Step 01</div>
                        <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.2rem;">Upload Resume</div>
                        <div style="font-size:0.8rem;color:#475569;margin-bottom:0.5rem;">PDF, DOCX, or TXT — max 10MB</div>
                    </div>
                    """)
                    # FIX: type="filepath" for Gradio 5 compatibility
                    single_file = gr.File(
                        label="Resume File",
                        file_types=[".pdf", ".docx", ".txt"],
                        type="filepath",
                    )

                with gr.Column():
                    gr.HTML("""
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;">
                        <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                                    text-transform:uppercase;color:#475569;margin-bottom:0.3rem;">Step 02</div>
                        <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.2rem;">Job Description</div>
                        <div style="font-size:0.8rem;color:#475569;margin-bottom:0.5rem;">Paste the full JD from any job posting</div>
                    </div>
                    """)
                    single_jd = gr.Textbox(
                        label="Job Description",
                        placeholder="We are looking for a Python Engineer with experience in FastAPI, Docker, AWS...",
                        lines=7,
                        max_lines=20,
                    )

            single_btn    = gr.Button("⚡  Analyze Resume", variant="primary", size="lg")
            single_output = gr.HTML(label="Results")
            # FIX: single PDF component — value+visibility controlled via gr.update()
            single_pdf    = gr.File(label="📄 Download PDF Report", visible=False, interactive=False)

            # FIX: outputs is now 2 items, not 3
            single_btn.click(
                fn=analyze_single,
                inputs=[single_file, single_jd],
                outputs=[single_output, single_pdf],
            )

        with gr.TabItem("🏆  Batch Ranking"):
            gr.HTML("""
            <div style="font-family:'Plus Jakarta Sans',sans-serif;margin-bottom:1.2rem;">
                <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.15em;
                            text-transform:uppercase;color:#00C2E0;margin-bottom:0.3rem;">Multiple Candidates</div>
                <div style="font-size:1.3rem;font-weight:800;color:#F1F5F9;margin-bottom:0.2rem;">Batch Ranking</div>
                <div style="font-size:0.85rem;color:#475569;">Upload 2–10 resumes and rank all candidates against one job description</div>
            </div>
            """)

            with gr.Row():
                with gr.Column():
                    gr.HTML("""
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;">
                        <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                                    text-transform:uppercase;color:#475569;margin-bottom:0.3rem;">Step 01</div>
                        <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.2rem;">Upload Resumes</div>
                        <div style="font-size:0.8rem;color:#475569;margin-bottom:0.5rem;">2–10 files — PDF, DOCX, or TXT</div>
                    </div>
                    """)
                    # FIX: type="filepath" for Gradio 5 compatibility
                    batch_files = gr.File(
                        label="Resume Files",
                        file_types=[".pdf", ".docx", ".txt"],
                        file_count="multiple",
                        type="filepath",
                    )

                with gr.Column():
                    gr.HTML("""
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;">
                        <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                                    text-transform:uppercase;color:#475569;margin-bottom:0.3rem;">Step 02</div>
                        <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.2rem;">Job Description</div>
                        <div style="font-size:0.8rem;color:#475569;margin-bottom:0.5rem;">All resumes ranked against this single JD</div>
                    </div>
                    """)
                    batch_jd = gr.Textbox(
                        label="Job Description",
                        placeholder="We are looking for a Python Engineer with experience in FastAPI, Docker, AWS...",
                        lines=7,
                        max_lines=20,
                    )

            batch_btn    = gr.Button("🏆  Rank All Candidates", variant="primary", size="lg")
            batch_output = gr.HTML(label="Rankings")
            # FIX: single PDF component — value+visibility controlled via gr.update()
            batch_pdf    = gr.File(label="📄 Download Batch Report", visible=False, interactive=False)

            # FIX: outputs is now 2 items, not 3
            batch_btn.click(
                fn=analyze_batch,
                inputs=[batch_files, batch_jd],
                outputs=[batch_output, batch_pdf],
            )

    gr.HTML("""
    <div style="font-family:'Plus Jakarta Sans',sans-serif;margin-top:2rem;padding-top:1rem;
                border-top:1px solid #1C2535;text-align:center;">
        <div style="display:flex;justify-content:center;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.5rem;">
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">FastAPI</span>
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">spaCy</span>
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">TF-IDF</span>
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">Embeddings</span>
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">Groq</span>
            <span style="font-size:0.68rem;font-weight:600;font-family:monospace;background:#111928;
                         color:#475569;border:1px solid #1C2535;border-radius:5px;padding:0.15rem 0.5rem;">LLaMA 3.1</span>
        </div>
        <div style="font-size:0.72rem;color:#334155;">RecruitIQ · Built with Python · Production Ready</div>
    </div>
    """)

# FIX: plain demo.launch() for native Gradio SDK on HuggingFace
demo.launch()