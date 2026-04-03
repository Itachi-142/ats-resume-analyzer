<div align="center">

# 🎯 RecruitIQ — ATS Resume Analyzer

**AI-powered resume screening with keyword scoring, semantic matching, and recruiter-grade feedback**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-HuggingFace-FFD700?style=for-the-badge)](https://spirit24-ats-resume-ui.hf.space)
[![API Docs](https://img.shields.io/badge/📡_API_Docs-Swagger_UI-00C2E0?style=for-the-badge)](https://spirit24-ats-resume-api.hf.space/docs)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gradio](https://img.shields.io/badge/Gradio-5.x-FF7C00?style=for-the-badge&logo=gradio&logoColor=white)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> RecruitIQ is a production-ready ATS (Applicant Tracking System) resume analyzer that combines **TF-IDF keyword scoring**, **semantic similarity embeddings**, and **Groq LLaMA 3.1** to deliver structured, recruiter-grade feedback on any resume — instantly.

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Multi-format Resume Parsing** | Supports PDF, DOCX, and TXT via PyMuPDF and python-docx |
| 🔑 **TF-IDF Keyword Scoring** | Weighted keyword matching with 200+ skills dictionary and 40+ aliases |
| 🧠 **Semantic Similarity** | Sentence-transformers `all-MiniLM-L6-v2` for deep contextual matching |
| 🤖 **AI Recruiter Feedback** | Structured JSON feedback via Groq LLaMA 3.1 with graceful fallback |
| 📊 **Confidence Scoring** | Composite score across keyword, semantic, and confidence dimensions |
| 🏆 **Batch Ranking** | Rank 2–10 candidates against a single job description simultaneously |
| 📥 **PDF Report Export** | Professional dark-themed PDF reports generated with ReportLab |
| ⚡ **Async FastAPI Backend** | High-performance async endpoints with CORS support |
| 🌐 **Gradio Frontend** | Professional dark UI deployed natively on HuggingFace Spaces |

---

## 🖥️ Live Demo

| Service | URL | Status |
|---|---|---|
| 🎨 Frontend UI | [spirit24-ats-resume-ui.hf.space](https://spirit24-ats-resume-ui.hf.space) | ✅ Live |
| ⚙️ Backend API | [spirit24-ats-resume-api.hf.space](https://spirit24-ats-resume-api.hf.space) | ✅ Live |
| 📡 API Docs | [/docs](https://spirit24-ats-resume-api.hf.space/docs) | ✅ Live |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│           Gradio Frontend (HuggingFace Spaces)           │
│   • Dark Professional UI    • File Upload                │
│   • Score Cards             • PDF Download               │
│   • Batch Ranking Table     • Skill Tags                 │
└──────────────────────┬──────────────────────────────────┘
                       │  multipart/form-data
┌──────────────────────▼──────────────────────────────────┐
│           FastAPI Backend (HuggingFace Spaces)           │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Parser    │  │   TF-IDF   │  │    Semantic     │  │
│  │  Service    │  │   Scoring  │  │   Similarity    │  │
│  │ PDF/DOCX/   │  │ 200+ Skills│  │  MiniLM-L6-v2  │  │
│  │   TXT       │  │  +Aliases  │  │   Embeddings    │  │
│  └──────┬──────┘  └──────┬─────┘  └────────┬────────┘  │
│         └────────────────┼─────────────────┘            │
│                          │                               │
│         ┌────────────────▼────────────────┐             │
│         │    Confidence Score Calculator   │             │
│         └────────────────┬────────────────┘             │
│                          │                               │
│         ┌────────────────▼────────────────┐             │
│         │  Groq LLaMA 3.1 — Structured    │             │
│         │  JSON Feedback + Fallback        │             │
│         └─────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
RecruitIQ/
├── 📁 Backend (ats-resume-api)
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routes/
│   │   ├── resume_routes.py       # POST /api/v1/analyze
│   │   └── batch_routes.py        # POST /api/v1/batch-analyze
│   ├── services/
│   │   ├── parser_service.py      # PDF/DOCX/TXT parsing
│   │   ├── pre_processing.py      # Text cleaning
│   │   ├── skill_service.py       # Skill extraction (200+ skills)
│   │   ├── semantic_service.py    # Sentence-transformers embeddings
│   │   ├── scoring_service.py     # TF-IDF + composite scoring
│   │   ├── feedback_service.py    # Groq LLaMA feedback
│   │   ├── nlp_service.py         # spaCy NLP pipeline
│   │   └── pdf_support_service.py # ReportLab PDF generation
│   └── models/
│       └── schemas.py             # Pydantic request/response models
│
└── 📁 Frontend (ats-resume-ui)
    ├── app.py                     # Gradio UI + API client
    ├── requirements.txt
    └── README.md
```

---

## 🔌 API Reference

### `POST /api/v1/analyze` — Single Resume Analysis

**Request** (`multipart/form-data`):
```
file            → Resume file (PDF, DOCX, TXT)
job_description → Job description text (string)
```

**Response**:
```json
{
  "scores": {
    "keyword":    0.50,
    "semantic":   0.62,
    "final":      0.57,
    "confidence": 0.81
  },
  "matched_skills": ["python", "fastapi", "sql"],
  "missing_skills": ["docker", "aws", "kubernetes"],
  "feedback": {
    "summary":        "Candidate has strong backend skills...",
    "strengths":      ["Proficiency in Python...", "Experience with REST APIs..."],
    "improvements":   ["No experience with Docker...", "Missing cloud skills..."],
    "recommendation": "Maybe - Interview with Reservations"
  }
}
```

### `POST /api/v1/batch-analyze` — Batch Candidate Ranking

**Request** (`multipart/form-data`):
```
files[]         → Multiple resume files (2–10)
job_description → Job description text (string)
```

**Response**: Ranked list of all candidates with individual scores and feedback.

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | FastAPI + Python (async) | High-performance REST API |
| **NLP** | spaCy | Text preprocessing and entity extraction |
| **Keyword Scoring** | TF-IDF (scikit-learn) | Weighted skill matching |
| **Semantic Scoring** | sentence-transformers `all-MiniLM-L6-v2` | Contextual similarity |
| **LLM** | Groq API — LLaMA 3.1 8B Instant | Structured recruiter feedback |
| **Resume Parsing** | PyMuPDF + python-docx | PDF and DOCX file support |
| **Frontend** | Gradio 5.x | Dark-themed interactive UI |
| **PDF Reports** | ReportLab | Professional PDF generation |
| **Deployment** | HuggingFace Spaces | Backend (Docker) + Frontend (Gradio SDK) |

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.10+
- Groq API key → [Get one free at console.groq.com](https://console.groq.com)

### 1. Clone the Repositories

```bash
# Backend
git clone https://huggingface.co/spaces/Spirit24/ats-resume-api
cd ats-resume-api

# Frontend (separate terminal)
git clone https://huggingface.co/spaces/Spirit24/ats-resume-ui
cd ats-resume-ui
```

### 2. Backend Setup

```bash
cd ats-resume-api

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env

# Start the API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

✅ API running at: `http://localhost:8000`
✅ Swagger docs at: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd ats-resume-ui

# Install dependencies
pip install -r requirements.txt

# Point to local backend
export API_BASE_URL=http://localhost:8000    # Mac/Linux
set API_BASE_URL=http://localhost:8000       # Windows

# Start the UI
python app.py
```

✅ Frontend running at: `http://localhost:7860`

---

## 📊 Score Interpretation

| Score Range | Label | Hiring Decision |
|---|---|---|
| 80 – 100% | 🟢 **Excellent** | ✅ Strong Yes — Advance to Interview |
| 65 – 79% | 🔵 **Good** | ✅ Yes — Schedule Interview |
| 50 – 64% | 🟡 **Fair** | ~ Maybe — Interview with Reservations |
| 35 – 49% | 🔴 **Weak** | ✕ No — Does Not Meet Requirements |
| 0 – 34% | 🔴 **Poor** | ✕ Strong No — Significant Skills Gap |

---

## 🌐 Deployment on HuggingFace Spaces

Both services are deployed on HuggingFace Spaces free tier:

| Space | SDK | Purpose |
|---|---|---|
| `Spirit24/ats-resume-api` | Docker | FastAPI backend |
| `Spirit24/ats-resume-ui` | Gradio | Frontend UI |

### Environment Variables

**Backend** (`ats-resume-api` → Settings → Secrets):
```
GROQ_API_KEY = your_groq_api_key_here
```

**Frontend** (`ats-resume-ui` → Settings → Variables):
```
API_BASE_URL = https://spirit24-ats-resume-api.hf.space
```

---

## 🗺️ Roadmap

- [x] Single resume analysis
- [x] Batch candidate ranking (up to 10)
- [x] PDF report export
- [x] Professional dark UI with glow effects
- [x] HuggingFace Spaces deployment
- [ ] User authentication and analysis history
- [ ] Resume improvement suggestions with examples
- [ ] ATS score simulator for different job boards
- [ ] Chrome extension for one-click job analysis
- [ ] LinkedIn profile URL support

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with 🔥 Python · FastAPI · Groq LLaMA 3.1 · Deployed on HuggingFace**

[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spirit24-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/Spirit24)

**⭐ Star this repo if you found it useful! ⭐**

</div>
