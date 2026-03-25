# ✅ FIXED
import logging
import spacy

logger = logging.getLogger(__name__)

# Load with a clear error message if model isn't installed
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Run: python -m spacy download en_core_web_sm"
    )

def preprocess_with_spacy(text: str) -> str:
    """
    Tokenize, remove stopwords and punctuation, then lemmatize.
    Used for NLP-quality preprocessing (skill extraction, etc.)
    """
    if not text or not text.strip():
        return ""

    doc = nlp(text.lower())
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop and not token.is_punct and token.lemma_.strip()
    ]
    return " ".join(tokens)