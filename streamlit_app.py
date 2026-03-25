import streamlit as st
import requests
import time

import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL   = os.getenv("API_BASE_URL", "http://localhost:8000")
SINGLE_API_URL = f"{API_BASE_URL}/api/v1/analyze"
BATCH_API_URL  = f"{API_BASE_URL}/api/v1/batch-analyze"



# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RecruitIQ — ATS Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
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
    --amber-dim:     rgba(245,158,11,0.12);
    --blue:          #3B82F6;
    --blue-dim:      rgba(59,130,246,0.12);
    --purple:        #8B5CF6;
    --text-primary:  #F1F5F9;
    --text-secondary:#94A3B8;
    --text-muted:    #475569;
    --font:          'Plus Jakarta Sans', sans-serif;
    --mono:          'JetBrains Mono', monospace;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: var(--font);
    background: var(--bg-primary);
    color: var(--text-primary);
}

.stApp { background: var(--bg-primary); }
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }

/* ── Main content ── */
.block-container {
    padding: 1.5rem 2rem 4rem 2rem !important;
    max-width: 1100px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div {
    padding: 1.5rem 1.2rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    width: fit-content;
    margin-bottom: 2rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 9px;
    color: var(--text-muted);
    font-family: var(--font);
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0.5rem 1.4rem;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: var(--cyan) !important;
    color: var(--bg-primary) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card);
    border: 1.5px dashed var(--border-active);
    border-radius: 14px;
    padding: 0.5rem;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--cyan);
    background: var(--bg-hover);
}
[data-testid="stFileUploader"] label { display: none !important; }

/* ── Text Area ── */
.stTextArea textarea {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
    line-height: 1.65 !important;
    padding: 1rem 1.1rem !important;
    resize: vertical !important;
    transition: all 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px var(--cyan-dim) !important;
    background: var(--bg-hover) !important;
}
.stTextArea label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--cyan) !important;
    color: var(--bg-primary) !important;
    font-family: var(--font) !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px var(--cyan-glow) !important;
    filter: brightness(1.1) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download Button ── */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    color: var(--cyan) !important;
    border: 1.5px solid var(--cyan) !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: var(--cyan-dim) !important;
    box-shadow: 0 4px 16px var(--cyan-dim) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: var(--text-secondary) !important;
    padding: 0.9rem 1.2rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--cyan); }

/* ── Custom Components ── */

/* Page header */
.page-header {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.page-header-eyebrow {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--cyan); margin-bottom: 0.4rem;
}
.page-header-title {
    font-size: 1.8rem; font-weight: 800; color: var(--text-primary);
    line-height: 1.2; margin-bottom: 0.4rem;
}
.page-header-sub {
    font-size: 0.88rem; color: var(--text-muted); font-weight: 400;
}

/* Input labels */
.input-label {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;
}
.input-title {
    font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;
}
.input-hint { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem; }

/* Status pill */
.status-pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--green-dim); color: var(--green);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.75rem; font-weight: 600;
    margin-top: 0.4rem;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.8rem 0;
}

/* ── Score Cards ── */
.score-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0.9rem; margin-bottom: 1.5rem;
}
.score-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.score-card:hover { border-color: var(--border-active); transform: translateY(-1px); }
.score-card-accent {
    position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 14px 14px 0 0;
}
.score-card-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;
}
.score-card-value {
    font-size: 2rem; font-weight: 800; line-height: 1; margin-bottom: 0.3rem;
}
.score-card-interp {
    font-size: 0.7rem; font-weight: 500; margin-bottom: 0.7rem;
}
.score-bar-track {
    height: 3px; border-radius: 2px; background: var(--border);
    overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 2px; }

/* ── Skills ── */
.skills-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; margin-bottom: 1.5rem; }
.skills-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.2rem;
}
.skills-card-header {
    display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.9rem;
}
.skills-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.skills-card-title {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
}
.skills-count {
    margin-left: auto; font-size: 0.7rem; font-weight: 600;
    font-family: var(--mono); padding: 0.1rem 0.5rem;
    border-radius: 6px;
}
.skills-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.skill-tag {
    display: inline-flex; align-items: center;
    padding: 0.2rem 0.65rem; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600;
    font-family: var(--mono); letter-spacing: 0.02em;
}
.skill-tag.matched {
    background: var(--green-dim); color: var(--green);
    border: 1px solid rgba(16,185,129,0.2);
}
.skill-tag.missing {
    background: var(--red-dim); color: var(--red);
    border: 1px solid rgba(239,68,68,0.2);
}
.no-skills { font-size: 0.82rem; color: var(--text-muted); font-style: italic; }

/* ── Section header ── */
.section-header {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--cyan); margin: 1.5rem 0 0.9rem 0;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-header::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
}

/* ── Feedback ── */
.summary-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
    border-radius: 0 14px 14px 0; padding: 1.2rem 1.4rem; margin-bottom: 0.9rem;
}
.summary-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;
}
.summary-text { font-size: 0.92rem; color: var(--text-secondary); line-height: 1.7; }

.fb-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.2rem; height: 100%; margin-bottom: 0.9rem;
}
.fb-card-title {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 0.8rem;
}
.fb-item {
    display: flex; gap: 0.6rem; margin-bottom: 0.75rem;
    font-size: 0.86rem; color: var(--text-secondary); line-height: 1.55;
    align-items: flex-start;
}
.fb-bullet { flex-shrink: 0; margin-top: 0.25rem; font-size: 0.7rem; }

/* ── Recommendation ── */
.rec-card {
    display: flex; align-items: center; gap: 1rem;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1rem 1.4rem;
    flex-wrap: wrap;
}
.rec-label-text {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-muted); white-space: nowrap;
}
.rec-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.45rem 1.1rem; border-radius: 8px;
    font-weight: 700; font-size: 0.85rem; letter-spacing: 0.02em;
}

/* ── Ranking ── */
.rank-header {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-bottom: none;
    border-radius: 14px 14px 0 0;
    padding: 0.7rem 1.1rem;
}
.rank-grid {
    display: grid;
    grid-template-columns: 50px 1.8fr 0.8fr 0.8fr 0.8fr 1.6fr;
    gap: 0.5rem; align-items: center;
}
.rank-col-hdr {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--text-muted); text-align: center;
}
.rank-col-hdr-left {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--text-muted);
}
.rank-row {
    background: var(--bg-card);
    border-left: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 0.85rem 1.1rem;
    transition: background 0.15s;
}
.rank-row:hover { background: var(--bg-hover); }
.rank-row-last {
    background: var(--bg-card);
    border-left: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    border-radius: 0 0 14px 14px;
    padding: 0.85rem 1.1rem;
    transition: background 0.15s;
}
.rank-row-last:hover { background: var(--bg-hover); }

/* ── Error ── */
.error-box {
    background: var(--red-dim); border: 1px solid rgba(239,68,68,0.25);
    border-radius: 10px; padding: 0.9rem 1.2rem; color: var(--red);
    font-size: 0.86rem; margin-top: 0.8rem; line-height: 1.5;
}

/* ── Sidebar components ── */
.sidebar-logo {
    font-size: 1.3rem; font-weight: 800; color: var(--text-primary);
    margin-bottom: 0.2rem; letter-spacing: -0.02em;
}
.sidebar-logo span { color: var(--cyan); }
.sidebar-version {
    font-size: 0.68rem; color: var(--text-muted); font-family: var(--mono);
    margin-bottom: 1.5rem;
}
.sidebar-divider {
    height: 1px; background: var(--border); margin: 1rem 0;
}
.sidebar-section {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.6rem;
}
.sidebar-stat {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.4rem 0; border-bottom: 1px solid var(--border);
}
.sidebar-stat-label { font-size: 0.8rem; color: var(--text-secondary); }
.sidebar-stat-value { font-size: 0.8rem; font-weight: 700; color: var(--cyan); font-family: var(--mono); }
.sidebar-info {
    font-size: 0.78rem; color: var(--text-muted); line-height: 1.6;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.8rem 0.9rem; margin-top: 0.5rem;
}
.sidebar-tech {
    display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.5rem;
}
.sidebar-badge {
    font-size: 0.68rem; font-weight: 600; font-family: var(--mono);
    background: var(--bg-card); color: var(--text-muted);
    border: 1px solid var(--border); border-radius: 5px;
    padding: 0.15rem 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────────────────────────

def score_label(score: float) -> tuple[str, str]:
    """Returns (label, color) for a given score."""
    if score >= 0.80: return "Excellent", "#10B981"
    if score >= 0.65: return "Good",      "#3B82F6"
    if score >= 0.50: return "Fair",      "#F59E0B"
    if score >= 0.35: return "Weak",      "#EF4444"
    return "Poor", "#EF4444"

def get_rec_colors(rec: str) -> tuple[str, str]:
    """Returns (text_color, bg_color) for recommendation."""
    return {
        "Strong Yes - Advance to Interview":   ("#10B981", "rgba(16,185,129,0.12)"),
        "Yes - Schedule Interview":            ("#3B82F6", "rgba(59,130,246,0.12)"),
        "Maybe - Interview with Reservations": ("#F59E0B", "rgba(245,158,11,0.12)"),
        "No - Does Not Meet Requirements":     ("#EF4444", "rgba(239,68,68,0.10)"),
        "Strong No - Significant Skills Gap":  ("#EF4444", "rgba(180,40,40,0.10)"),
    }.get(rec, ("#F59E0B", "rgba(245,158,11,0.12)"))

def get_rec_icon(rec: str) -> str:
    return {
        "Strong Yes - Advance to Interview":   "✓",
        "Yes - Schedule Interview":            "✓",
        "Maybe - Interview with Reservations": "~",
        "No - Does Not Meet Requirements":     "✕",
        "Strong No - Significant Skills Gap":  "✕",
    }.get(rec, "~")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">Recruit<span>IQ</span></div>
    <div class="sidebar-version">v2.0 · ATS Resume Analyzer</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">How It Works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-info">
        Upload a resume and paste a job description. The system extracts skills,
        computes keyword and semantic similarity, then generates structured
        recruiter-grade feedback using AI.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Score Guide</div>', unsafe_allow_html=True)

    for label, color, desc in [
        ("80–100%", "#10B981", "Excellent match"),
        ("65–79%",  "#3B82F6", "Good match"),
        ("50–64%",  "#F59E0B", "Fair match"),
        ("35–49%",  "#EF4444", "Weak match"),
        ("0–34%",   "#EF4444", "Poor match"),
    ]:
        st.markdown(f"""
        <div class="sidebar-stat">
            <span class="sidebar-stat-label">{desc}</span>
            <span class="sidebar-stat-value" style="color:{color};">{label}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Powered By</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-tech">
        <span class="sidebar-badge">FastAPI</span>
        <span class="sidebar-badge">spaCy</span>
        <span class="sidebar-badge">TF-IDF</span>
        <span class="sidebar-badge">Embeddings</span>
        <span class="sidebar-badge">Groq</span>
        <span class="sidebar-badge">LLaMA 3.1</span>
        <span class="sidebar-badge">reportlab</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.72rem;color:#334155;text-align:center;margin-top:0.5rem;">
        Built with Python · Production Ready
    </div>
    """, unsafe_allow_html=True)


# ── Shared Render Functions ───────────────────────────────────────────────────

def render_score_cards(scores: dict):
    configs = [
        ("Overall Score",  "final",      "#00C2E0", "linear-gradient(90deg,#00C2E0,#0891B2)"),
        ("Keyword Match",  "keyword",    "#10B981", "linear-gradient(90deg,#10B981,#059669)"),
        ("Semantic Match", "semantic",   "#3B82F6", "linear-gradient(90deg,#3B82F6,#2563EB)"),
        ("Confidence",     "confidence", "#F59E0B", "linear-gradient(90deg,#F59E0B,#D97706)"),
    ]
    cols = st.columns(4, gap="small")
    for col, (label, key, color, grad) in zip(cols, configs):
        val   = scores[key]
        pct   = int(val * 100)
        interp, icolor = score_label(val)
        with col:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-card-accent" style="background:{grad};"></div>
                <div class="score-card-label">{label}</div>
                <div class="score-card-value" style="color:{color};">{pct}%</div>
                <div class="score-card-interp" style="color:{icolor};">{interp}</div>
                <div class="score-bar-track">
                    <div class="score-bar-fill" style="width:{pct}%;background:{grad};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_skills(matched: list, missing: list):
    col1, col2 = st.columns(2, gap="small")

    with col1:
        tags = "".join(
            f'<span class="skill-tag matched">{s}</span>' for s in matched
        ) if matched else '<span class="no-skills">None detected</span>'
        st.markdown(f"""
        <div class="skills-card">
            <div class="skills-card-header">
                <div class="skills-dot" style="background:#10B981;"></div>
                <div class="skills-card-title" style="color:#10B981;">Matched Skills</div>
                <div class="skills-count" style="background:rgba(16,185,129,0.1);color:#10B981;">{len(matched)}</div>
            </div>
            <div class="skills-tags">{tags}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        tags = "".join(
            f'<span class="skill-tag missing">{s}</span>' for s in missing
        ) if missing else '<span class="no-skills">No gaps — perfect match ✓</span>'
        st.markdown(f"""
        <div class="skills-card">
            <div class="skills-card-header">
                <div class="skills-dot" style="background:#EF4444;"></div>
                <div class="skills-card-title" style="color:#EF4444;">Missing Skills</div>
                <div class="skills-count" style="background:rgba(239,68,68,0.1);color:#EF4444;">{len(missing)}</div>
            </div>
            <div class="skills-tags">{tags}</div>
        </div>
        """, unsafe_allow_html=True)


def render_feedback(feedback: dict):
    # Summary
    st.markdown(f"""
    <div class="summary-card">
        <div class="summary-label">Recruiter Summary</div>
        <div class="summary-text">{feedback["summary"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Strengths & Improvements
    col1, col2 = st.columns(2, gap="small")
    with col1:
        items = "".join(
            f'<div class="fb-item"><span class="fb-bullet" style="color:#10B981;">▸</span>'
            f'<span>{s}</span></div>'
            for s in feedback["strengths"]
        )
        st.markdown(f"""
        <div class="fb-card">
            <div class="fb-card-title" style="color:#10B981;">Strengths</div>
            {items}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        items = "".join(
            f'<div class="fb-item"><span class="fb-bullet" style="color:#EF4444;">▸</span>'
            f'<span>{i}</span></div>'
            for i in feedback["improvements"]
        )
        st.markdown(f"""
        <div class="fb-card">
            <div class="fb-card-title" style="color:#EF4444;">Areas to Improve</div>
            {items}
        </div>
        """, unsafe_allow_html=True)

    # Recommendation
    rec    = feedback["recommendation"]
    color, bg = get_rec_colors(rec)
    icon   = get_rec_icon(rec)
    st.markdown(f"""
    <div class="rec-card">
        <div class="rec-label-text">Hiring Recommendation</div>
        <div class="rec-badge" style="color:{color};background:{bg};border:1.5px solid {color};">
            {icon}&nbsp; {rec}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Single Mode ───────────────────────────────────────────────────────────────

def render_single_mode():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-eyebrow">Single Candidate</div>
        <div class="page-header-title">Resume Analysis</div>
        <div class="page-header-sub">Upload one resume and evaluate it against a job description</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="input-label">Step 01</div>
        <div class="input-title">Upload Resume</div>
        <div class="input-hint">PDF, DOCX, or TXT — max 5MB</div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            label="resume", type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            kb = len(uploaded_file.getvalue()) / 1024
            st.markdown(
                f'<div class="status-pill">✓ {uploaded_file.name} · {kb:.1f} KB</div>',
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("""
        <div class="input-label">Step 02</div>
        <div class="input-title">Job Description</div>
        <div class="input-hint">Paste the full JD from any job posting</div>
        """, unsafe_allow_html=True)
        jd = st.text_area(
            label="jd", height=170,
            placeholder="We are looking for a Python Engineer with experience in FastAPI, Docker, AWS...",
            label_visibility="collapsed",
        )
        if jd:
            n = len(jd)
            c = "#10B981" if n >= 100 else "#F59E0B"
            t = f"✓ {n} characters" if n >= 100 else f"{n} chars — add more detail"
            st.markdown(f'<div style="font-size:0.75rem;color:{c};margin-top:0.3rem;">{t}</div>',
                        unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        clicked = st.button("⚡  Analyze Resume", use_container_width=True)

    if clicked:
        if not uploaded_file:
            st.markdown('<div class="error-box">⚠ Please upload a resume file.</div>', unsafe_allow_html=True)
        elif not jd.strip():
            st.markdown('<div class="error-box">⚠ Please paste a job description.</div>', unsafe_allow_html=True)
        elif len(jd.strip()) < 50:
            st.markdown('<div class="error-box">⚠ Job description too short — add more detail.</div>', unsafe_allow_html=True)
        else:
            with st.spinner("Analyzing resume..."):
                try:
                    response = requests.post(
                        SINGLE_API_URL,
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")},
                        data={"job_description": jd},
                        timeout=120,
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

                    # Scores
                    st.markdown('<div class="section-header">Analysis Scores</div>', unsafe_allow_html=True)
                    render_score_cards(result["scores"])

                    # Skills
                    st.markdown('<div class="section-header">Skill Analysis</div>', unsafe_allow_html=True)
                    render_skills(result["matched_skills"], result["missing_skills"])

                    # Feedback
                    st.markdown('<div class="section-header">Recruiter Feedback</div>', unsafe_allow_html=True)
                    render_feedback(result["feedback"])

                    # Actions
                    st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
                    try:
                        from services.pdf_support_service import generate_pdf_report
                        pdf = generate_pdf_report(result, uploaded_file.name)
                        st.download_button(
                            label="⬇  Download PDF Report",
                            data=pdf,
                            file_name=f"RecruitIQ_{uploaded_file.name.rsplit('.',1)[0]}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.markdown(f'<div class="error-box">⚠ PDF error: {e}</div>', unsafe_allow_html=True)

                    with st.expander("Raw JSON Response"):
                        st.json(result)

                except requests.exceptions.ConnectionError:
                    st.markdown(
                        '<div class="error-box">⚠ Cannot reach API server. '
                        'Run: <code>python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload</code></div>',
                        unsafe_allow_html=True,
                    )
                except requests.exceptions.HTTPError as e:
                    try: detail = e.response.json().get("detail", str(e))
                    except: detail = str(e)
                    st.markdown(f'<div class="error-box">⚠ API Error: {detail}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-box">⚠ Error: {e}</div>', unsafe_allow_html=True)


# ── Batch Mode ────────────────────────────────────────────────────────────────

def render_ranking_table(candidates: list):
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    # Header
    st.markdown("""
    <div class="rank-header">
        <div class="rank-grid">
            <div class="rank-col-hdr">Rank</div>
            <div class="rank-col-hdr-left">Candidate</div>
            <div class="rank-col-hdr">Overall</div>
            <div class="rank-col-hdr">Keyword</div>
            <div class="rank-col-hdr">Semantic</div>
            <div class="rank-col-hdr">Verdict</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    total = len(candidates)
    for c in candidates:
        medal    = medals.get(c["rank"], f"#{c['rank']}")
        score    = int(c["scores"]["final"]    * 100)
        keyword  = int(c["scores"]["keyword"]  * 100)
        semantic = int(c["scores"]["semantic"] * 100)
        rec      = c["feedback"]["recommendation"]
        color, bg = get_rec_colors(rec)
        icon     = get_rec_icon(rec)
        name     = c["filename"].rsplit(".", 1)[0][:38]
        row_cls  = "rank-row-last" if c["rank"] == total else "rank-row"
        _, score_color = score_label(c["scores"]["final"])

        st.markdown(f"""
        <div class="{row_cls}">
            <div class="rank-grid">
                <div style="text-align:center;font-size:1.2rem;">{medal}</div>
                <div style="font-weight:600;color:#F1F5F9;font-size:0.88rem;">{name}</div>
                <div style="text-align:center;font-weight:800;font-size:1.05rem;color:{score_color};">{score}%</div>
                <div style="text-align:center;font-weight:600;color:#10B981;">{keyword}%</div>
                <div style="text-align:center;font-weight:600;color:#3B82F6;">{semantic}%</div>
                <div style="text-align:center;">
                    <span style="color:{color};background:{bg};border:1px solid {color};
                                 border-radius:6px;padding:0.2rem 0.7rem;
                                 font-size:0.72rem;font-weight:700;">{icon} {rec}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)


def render_candidate_card(candidate: dict):
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank   = candidate["rank"]
    score  = int(candidate["scores"]["final"] * 100)
    medal  = medals.get(rank, f"#{rank}")
    _, sc  = score_label(candidate["scores"]["final"])

    with st.expander(f"{medal}  Rank #{rank} — {candidate['filename']}  ·  {score}% overall"):
        render_score_cards(candidate["scores"])
        render_skills(candidate["matched_skills"], candidate["missing_skills"])
        st.markdown('<div class="section-header">Recruiter Feedback</div>', unsafe_allow_html=True)
        render_feedback(candidate["feedback"])


def render_batch_mode():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-eyebrow">Multiple Candidates</div>
        <div class="page-header-title">Batch Ranking</div>
        <div class="page-header-sub">Upload 2–10 resumes and rank all candidates against one job description</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="input-label">Step 01</div>
        <div class="input-title">Upload Resumes</div>
        <div class="input-hint">2–10 files — PDF, DOCX, or TXT — max 5MB each</div>
        """, unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            label="resumes", type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            st.markdown(
                f'<div class="status-pill">✓ {len(uploaded_files)} file(s) ready</div>',
                unsafe_allow_html=True,
            )
            for f in uploaded_files:
                kb = len(f.getvalue()) / 1024
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#475569;margin-left:0.3rem;margin-top:0.2rem;">'
                    f'· {f.name} ({kb:.1f} KB)</div>',
                    unsafe_allow_html=True,
                )

    with col2:
        st.markdown("""
        <div class="input-label">Step 02</div>
        <div class="input-title">Job Description</div>
        <div class="input-hint">All resumes ranked against this single JD</div>
        """, unsafe_allow_html=True)
        jd = st.text_area(
            label="jd_batch", height=170,
            placeholder="We are looking for a Python Engineer with experience in FastAPI, Docker, AWS...",
            label_visibility="collapsed",
        )
        if jd:
            n = len(jd)
            c = "#10B981" if n >= 100 else "#F59E0B"
            t = f"✓ {n} characters" if n >= 100 else f"{n} chars — add more detail"
            st.markdown(f'<div style="font-size:0.75rem;color:{c};margin-top:0.3rem;">{t}</div>',
                        unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        clicked = st.button("🏆  Rank All Candidates", use_container_width=True)

    if clicked:
        if not uploaded_files or len(uploaded_files) < 2:
            st.markdown('<div class="error-box">⚠ Upload at least 2 resumes to rank.</div>', unsafe_allow_html=True)
        elif len(uploaded_files) > 10:
            st.markdown('<div class="error-box">⚠ Maximum 10 resumes per batch.</div>', unsafe_allow_html=True)
        elif not jd.strip():
            st.markdown('<div class="error-box">⚠ Please paste a job description.</div>', unsafe_allow_html=True)
        else:
            with st.spinner(f"Ranking {len(uploaded_files)} candidates — this takes a moment..."):
                try:
                    response = requests.post(
                        BATCH_API_URL,
                        files=[("files", (f.name, f.getvalue(), "application/octet-stream")) for f in uploaded_files],
                        data={"job_description": jd},
                        timeout=600,
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="section-header">Candidate Rankings — {result["total_candidates"]} Analyzed</div>',
                        unsafe_allow_html=True,
                    )

                    render_ranking_table(result["candidates"])

                    st.markdown('<div class="section-header">Detailed Breakdown</div>', unsafe_allow_html=True)
                    for c in result["candidates"]:
                        render_candidate_card(c)

                    st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
                    try:
                        from services.pdf_support_service import generate_batch_pdf_report
                        pdf = generate_batch_pdf_report(result)
                        st.download_button(
                            label="⬇  Download Batch Ranking Report",
                            data=pdf,
                            file_name="RecruitIQ_Batch_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.markdown(f'<div class="error-box">⚠ PDF error: {e}</div>', unsafe_allow_html=True)

                    with st.expander("Raw JSON Response"):
                        st.json(result)

                except requests.exceptions.ConnectionError:
                    st.markdown(
                        '<div class="error-box">⚠ Cannot reach API server.</div>',
                        unsafe_allow_html=True,
                    )
                except requests.exceptions.HTTPError as e:
                    try: detail = e.response.json().get("detail", str(e))
                    except: detail = str(e)
                    st.markdown(f'<div class="error-box">⚠ API Error: {detail}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-box">⚠ Error: {e}</div>', unsafe_allow_html=True)


# ── App Layout ────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["🎯  Single Resume", "🏆  Batch Ranking"])

with tab1:
    render_single_mode()

with tab2:
    render_batch_mode()