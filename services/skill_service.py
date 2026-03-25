# services/skill_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Skill extraction with 200+ skills, aliases, and TF-IDF weighted scoring.
# ─────────────────────────────────────────────────────────────────────────────

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ── Master Skills Dictionary ──────────────────────────────────────────────────
# 200+ skills grouped by domain. All lowercase.

SKILLS: set[str] = {
    # ── Languages ──────────────────────────────────────────────────────────
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "perl", "haskell", "elixir", "dart", "julia",
    "bash", "shell", "powershell", "groovy", "lua", "assembly",

    # ── Web Frontend ────────────────────────────────────────────────────────
    "html", "css", "sass", "scss", "less",
    "react", "react.js", "angular", "vue", "vue.js", "svelte",
    "next.js", "nuxt.js", "gatsby", "remix",
    "jquery", "bootstrap", "tailwind", "tailwindcss",
    "webpack", "vite", "babel", "eslint",

    # ── Web Backend ─────────────────────────────────────────────────────────
    "node.js", "express", "fastapi", "flask", "django",
    "spring", "spring boot", "rails", "laravel", "asp.net",
    "graphql", "rest", "grpc", "websocket", "oauth",
    "nginx", "apache", "gunicorn", "uvicorn",

    # ── Data & ML ───────────────────────────────────────────────────────────
    "machine learning", "deep learning", "nlp", "computer vision",
    "ml", "ai", "artificial intelligence", "data science", "data analysis",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "xgboost", "lightgbm", "catboost", "hugging face", "transformers",
    "langchain", "llamaindex", "openai", "ollama",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "jupyter", "anaconda", "mlflow", "wandb", "dvc",
    "rag", "embeddings", "vector database", "semantic search",
    "reinforcement learning", "generative ai", "llm", "fine-tuning",
    "feature engineering", "model deployment", "a/b testing",

    # ── Databases ───────────────────────────────────────────────────────────
    "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle",
    "mongodb", "redis", "cassandra", "dynamodb", "couchdb", "neo4j",
    "elasticsearch", "opensearch", "pinecone", "chroma", "faiss",
    "supabase", "firebase", "realm",

    # ── Cloud & DevOps ──────────────────────────────────────────────────────
    "aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify",
    "docker", "kubernetes", "k8s", "helm", "istio",
    "terraform", "ansible", "puppet", "chef", "pulumi",
    "ci/cd", "jenkins", "github actions", "gitlab ci", "circle ci",
    "linux", "unix", "ubuntu", "centos", "debian",
    "git", "github", "gitlab", "bitbucket",
    "prometheus", "grafana", "datadog", "splunk", "elk",
    "cloudformation", "cdk", "serverless",

    # ── Data Engineering ────────────────────────────────────────────────────
    "spark", "hadoop", "kafka", "airflow", "dbt", "flink",
    "data pipeline", "etl", "data warehouse", "data lake",
    "snowflake", "bigquery", "redshift", "databricks",
    "tableau", "power bi", "looker", "metabase", "superset",

    # ── Mobile ──────────────────────────────────────────────────────────────
    "react native", "flutter", "android", "ios", "swift", "swiftui",
    "xamarin", "ionic", "cordova",

    # ── Embedded & Hardware ─────────────────────────────────────────────────
    "embedded", "rtos", "freertos", "spi", "i2c", "uart", "can", "modbus",
    "stm32", "arduino", "raspberry pi", "esp32", "esp8266",
    "fpga", "verilog", "vhdl", "labview", "plc",
    "iot", "mqtt", "zigbee", "bluetooth", "wifi",

    # ── Security ────────────────────────────────────────────────────────────
    "cybersecurity", "penetration testing", "ethical hacking",
    "owasp", "ssl", "tls", "jwt", "encryption", "firewall",
    "soc", "siem", "vulnerability assessment",

    # ── Process & Soft Skills ────────────────────────────────────────────────
    "agile", "scrum", "kanban", "waterfall", "safe",
    "jira", "confluence", "notion", "trello", "asana",
    "microservices", "system design", "api design",
    "unit testing", "integration testing", "tdd", "bdd",
    "pytest", "jest", "selenium", "cypress",
    "technical writing", "documentation",
}

# ── Skill Aliases ─────────────────────────────────────────────────────────────
# Maps common abbreviations and variants to canonical skill names.
# This dramatically improves matching accuracy.

ALIASES: dict[str, str] = {
    # Language aliases
    "js":           "javascript",
    "ts":           "typescript",
    "py":           "python",
    "golang":       "go",
    "c plus plus":  "c++",
    "cplusplus":    "c++",
    "csharp":       "c#",

    # Framework aliases
    "reactjs":      "react",
    "react js":     "react",
    "vuejs":        "vue",
    "vue js":       "vue",
    "nextjs":       "next.js",
    "next js":      "next.js",
    "nodejs":       "node.js",
    "node js":      "node.js",
    "expressjs":    "express",
    "springboot":   "spring boot",
    "sk-learn":     "scikit-learn",
    "sklearn":      "scikit-learn",

    # ML/AI aliases
    "ml":                   "machine learning",
    "ai":                   "artificial intelligence",
    "dl":                   "deep learning",
    "nlp":                  "nlp",
    "cv":                   "computer vision",
    "llms":                 "llm",
    "large language model": "llm",
    "genai":                "generative ai",
    "gen ai":               "generative ai",
    "rag":                  "rag",
    "hf":                   "hugging face",
    "huggingface":          "hugging face",

    # Cloud aliases
    "amazon web services":  "aws",
    "google cloud platform":"gcp",
    "google cloud":         "gcp",
    "microsoft azure":      "azure",
    "k8s":                  "kubernetes",
    "gha":                  "github actions",
    "gh actions":           "github actions",

    # DB aliases
    "pg":           "postgresql",
    "postgres":     "postgresql",
    "mongo":        "mongodb",
    "elastic":      "elasticsearch",

    # Tool aliases
    "tf":           "terraform",
    "powerbi":      "power bi",
    "power-bi":     "power bi",
    "tableau":      "tableau",
    "dbt":          "dbt",

    # Process aliases
    "ci cd":        "ci/cd",
    "cicd":         "ci/cd",
    "tdd":          "tdd",
    "bdd":          "bdd",
    "rest api":     "rest",
    "restful":      "rest",
    "restful api":  "rest",
}

# ── IDF Weights ───────────────────────────────────────────────────────────────
# Higher = rarer = more valuable match.
# Skills not listed use DEFAULT_IDF.

IDF_WEIGHTS: dict[str, float] = {
    # Very common — low weight
    "python":           1.2, "git":              1.1, "sql":              1.2,
    "linux":            1.3, "html":             1.1, "css":              1.1,
    "javascript":       1.2, "java":             1.2, "agile":            1.0,
    "scrum":            1.0, "artificial intelligence": 1.1,
    "machine learning": 1.3, "nlp":              1.5, "ml":               1.2,
    "data science":     1.4, "data analysis":    1.3, "rest":             1.4,
    "github":           1.3, "jira":             1.1, "jupyter":          1.3,
    "pandas":           1.5, "numpy":            1.5,

    # Medium weight
    "react":            1.6, "docker":           1.7, "aws":              1.7,
    "fastapi":          1.8, "flask":            1.6, "django":           1.6,
    "mongodb":          1.7, "postgresql":       1.6, "typescript":       1.6,
    "azure":            1.7, "gcp":              1.8, "tensorflow":       1.7,
    "pytorch":          1.8, "scikit-learn":     1.8, "deep learning":    1.6,
    "node.js":          1.7, "vue":              1.8, "angular":          1.7,
    "redis":            2.0, "elasticsearch":    1.9, "graphql":          2.0,
    "spark":            2.0, "kafka":            2.0, "airflow":          2.0,
    "snowflake":        2.0, "bigquery":         1.9, "databricks":       2.0,
    "tableau":          1.7, "power bi":         1.7,
    "next.js":          1.8, "tailwindcss":      1.7,
    "github actions":   1.9, "jenkins":          1.8, "ci/cd":            1.9,
    "computer vision":  1.8, "generative ai":    1.8, "llm":              1.9,
    "rag":              2.1, "embeddings":       2.0, "langchain":        2.1,
    "mlflow":           2.1, "hugging face":     2.0, "fine-tuning":      2.2,

    # High weight — rare/specialized
    "kubernetes":       2.2, "terraform":        2.3, "ansible":          2.2,
    "rust":             2.4, "scala":            2.2, "kotlin":           2.0,
    "go":               2.1, "fpga":             2.8, "verilog":          2.8,
    "vhdl":             2.8, "rtos":             2.6, "embedded":         2.2,
    "stm32":            2.7, "modbus":           2.6, "faiss":            2.4,
    "pinecone":         2.4, "dbt":              2.2, "flink":            2.3,
    "databricks":       2.1, "redshift":         2.1, "looker":           2.1,
    "cybersecurity":    2.2, "penetration testing": 2.5, "ethical hacking": 2.5,
    "reinforcement learning": 2.3, "llamaindex": 2.3, "openai":          1.9,
    "vector database":  2.3, "semantic search":  2.2, "system design":   2.0,
    "microservices":    1.9, "grpc":             2.1, "pulumi":           2.3,
}

DEFAULT_IDF   = 1.5
SHORT_SKILLS  = {"c", "r", "go"}


# ── Extraction Logic ──────────────────────────────────────────────────────────

def _normalize_aliases(text: str) -> str:
    """
    Replace known aliases with canonical skill names before extraction.
    Ensures 'k8s' matches 'kubernetes', 'js' matches 'javascript', etc.
    """
    for alias, canonical in sorted(ALIASES.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(alias)}\b"
        text    = re.sub(pattern, canonical, text, flags=re.IGNORECASE)
    return text


def _extract_raw_skills(text: str) -> set[str]:
    """Extract skills from cleaned + alias-normalized text."""
    if not text or not text.strip():
        return set()

    # Normalize aliases first
    text = _normalize_aliases(text.lower())
    found = set()

    # Multi-word skills (e.g. "machine learning", "deep learning", "spring boot")
    for skill in SKILLS:
        if " " in skill and skill in text:
            found.add(skill)

    # Single-word skills
    words = set(re.findall(r"\b[\w\+\#\.\-\/]+\b", text))
    for word in words:
        if word in SKILLS and word not in SHORT_SKILLS:
            found.add(word)

    # Short skills — strict boundary matching
    for short in SHORT_SKILLS:
        pattern = rf"(?<![a-z]){re.escape(short)}(?![a-z])"
        if re.search(pattern, text) and short in SKILLS:
            found.add(short)

    return found


# ── Scoring ───────────────────────────────────────────────────────────────────

def compute_tfidf_keyword_score(
    matched_skills: list[str],
    jd_skills:      set[str],
) -> float:
    """
    TF-IDF weighted keyword score.
    Rare/specialized skills contribute more than common ones.
    """
    if not jd_skills:
        return 0.0

    matched_weight  = sum(IDF_WEIGHTS.get(s, DEFAULT_IDF) for s in matched_skills)
    total_jd_weight = sum(IDF_WEIGHTS.get(s, DEFAULT_IDF) for s in jd_skills)

    if total_jd_weight == 0:
        return 0.0

    return round(min(matched_weight / total_jd_weight, 1.0), 4)


def compute_keyword_score(matched_skills: list, jd_skills_count: int) -> float:
    """Simple keyword score — kept for backwards compatibility."""
    if jd_skills_count == 0:
        return 0.0
    return round(len(matched_skills) / jd_skills_count, 4)


# ── Public Interface ──────────────────────────────────────────────────────────

def extract_skills(
    resume_text: str,
    job_text:    str,
) -> Tuple[list[str], list[str], set[str]]:
    """
    Extract and compare skills between resume and JD.

    Returns:
        matched_skills:  skills in both resume and JD (sorted list)
        missing_skills:  skills in JD but not resume (sorted list)
        jd_skills_set:   full JD skill set (for TF-IDF weighting)
    """
    resume_skills = _extract_raw_skills(resume_text)
    jd_skills     = _extract_raw_skills(job_text)

    if not jd_skills:
        logger.warning("No recognizable skills found in job description.")

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)

    logger.info(
        "Skills — JD: %d | Matched: %d | Missing: %d",
        len(jd_skills), len(matched), len(missing),
    )

    return matched, missing, jd_skills