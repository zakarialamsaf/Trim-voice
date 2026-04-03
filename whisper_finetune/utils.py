"""Text normalization and shared utilities."""

import re
import unicodedata


def normalize_text(text):
    """Normalize transcript text: lowercase, remove SIL/NOI markers and punctuation."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text)).lower()
    text = re.sub(r'\bSIL\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNOI\b', '', text, flags=re.IGNORECASE)
    text = text.replace("\u2019", "").replace("'", "")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
