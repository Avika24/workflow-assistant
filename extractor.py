"""Gemini extraction, JSON parsing, and one validation retry."""
import json
import os
import re
from datetime import date
from typing import Any
import google.generativeai as genai
from pydantic import ValidationError
from schemas import Analysis

class ExtractionError(RuntimeError):
    """Raised when Gemini cannot produce valid DocFlow output."""

def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

def _build_prompt(document_text: str, document_date: date) -> str:
    return f"""
You are DocFlow, a careful document workflow analyst.
Analyze ONLY the source document. Do not infer facts not stated.
Return one valid JSON object with exactly these keys:
{{
  "summary": "short paragraph",
  "key_points": ["point 1"],
  "action_items": [
    {{"task":"clear task","owner":"explicit owner or null","deadline":"YYYY-MM-DD or null",
      "priority":"high, medium, or low","evidence":"exact verbatim source quote"}}
  ],
  "key_dates": [{{"event":"what happens","date":"YYYY-MM-DD"}}]
}}
Rules:
- Document date: {document_date.isoformat()}.
- Resolve relative dates (e.g. next Friday) against the document date.
- Return null for unstated owners/deadlines.
- Every action item must have a short exact verbatim evidence quote.
- Include only source-supported action items; use [] when none exist.
- Dates must be valid ISO calendar dates.
- Return JSON only, without Markdown fences or commentary.
SOURCE DOCUMENT:
<document>
{document_text}
</document>
"""

def _parse_and_validate(raw: str) -> Analysis:
    return Analysis.model_validate(json.loads(_strip_json_fence(raw)))

def extract_analysis(document_text: str, document_date: date) -> Analysis:
    if not document_text.strip():
        raise ExtractionError("Please provide some document text.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ExtractionError("GEMINI_API_KEY is missing. Add it to your .env file and restart the app.")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    genai.configure(api_key=api_key, transport="rest")
    model = genai.GenerativeModel(model_name)
    prompt = _build_prompt(document_text, document_date)
    last_error = None
    for attempt in range(2):
        try:
            response = model.generate_content(prompt)
            raw = getattr(response, "text", None)
            if not raw:
                raise ValueError("Gemini returned an empty response.")
            return _parse_and_validate(raw)
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            last_error = exc
            if attempt == 0:
                prompt += "\n\nYour previous response was invalid. Return corrected JSON only, matching the schema and valid date formats."
                continue
            break
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "quota" in message or "rate" in message:
                raise ExtractionError("Gemini rate limit reached. Wait a little and try again.") from exc
            if "api key" in message or "permission" in message or "401" in message or "403" in message:
                raise ExtractionError("Gemini rejected the API key. Check GEMINI_API_KEY in your .env file.") from exc
            raise ExtractionError("Gemini request failed. Check your connection, model name, and API quota.") from exc
    raise ExtractionError("Gemini returned invalid structured output twice. Please try again.") from last_error

def analysis_to_dict(analysis: Analysis) -> dict[str, Any]:
    return analysis.model_dump(mode="json")
