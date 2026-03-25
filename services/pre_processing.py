# ✅ FIXED — pre_processing.py

import re


def clean_text(text: str) -> str:
    """
    Cleans raw resume/JD text for NLP processing.
    Preserves tech-relevant characters like +, #, . (for C++, C#, .NET)
    """
    if not text or not text.strip():
        return ""

    # Lowercase
    text = text.lower()

    # Keep alphanumeric + whitespace + tech-relevant special chars
    # Preserves: c++, c#, .net, node.js, scikit-learn
    text = re.sub(r"[^a-z0-9\s\+\#\.\-\_]", " ", text)

    # Collapse multiple spaces/newlines into single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()