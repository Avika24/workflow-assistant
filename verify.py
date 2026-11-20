"""Evidence quote verification. Presence does not prove task correctness."""
import re
from difflib import SequenceMatcher

def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()

def verify_quote(document_text: str, quote: str, threshold: float = 0.85) -> tuple[bool, float]:
    document = _normalize(document_text)
    candidate = _normalize(quote)
    if not candidate or not document:
        return False, 0.0
    if candidate in document:
        return True, 1.0
    words = document.split()
    quote_words = candidate.split()
    best = 0.0
    widths = {max(1, len(quote_words)-2), len(quote_words), len(quote_words)+2}
    for start in range(len(words)):
        for width in widths:
            window = " ".join(words[start:start+width])
            if window:
                best = max(best, SequenceMatcher(None, candidate, window).ratio())
            if best >= threshold:
                return True, best
    return best >= threshold, best

def verify_action_items(document_text: str, action_items: list) -> list[dict]:
    results = []
    for item in action_items:
        quote = item.evidence if hasattr(item, "evidence") else item.get("evidence", "")
        verified, similarity = verify_quote(document_text, quote)
        results.append({"verified": verified, "similarity": round(similarity, 3),
                        "warning": None if verified else "⚠ not found in source"})
    return results
