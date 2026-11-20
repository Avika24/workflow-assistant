"""Gemini extraction using the supported Google GenAI SDK."""
import json
import os
import re
from datetime import date
from typing import Any

from google import genai
from google.genai import types
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

Rules:
- The document date is {document_date.isoformat()}.
- Resolve relative dates (for example, "next Friday") using that document date.
- Return null for an owner or deadline that is not explicitly stated.
- Every action item must include a short, exact verbatim quote from the source.
- Include only action items supported by the source; use [] when none exist.
- Use YYYY-MM-DD for all dates. If a deadline cannot be resolved confidently,
  return null. Omit key dates that cannot be resolved to a valid date.
- Priority must be high, medium, or low.
- Return only JSON matching the supplied response schema.

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
        raise ExtractionError(
            "GEMINI_API_KEY is missing. Add it to your .env file and restart the app."
        )

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    prompt = _build_prompt(document_text, document_date)
    client = genai.Client(api_key=api_key)
    last_error: Exception | None = None

    try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=Analysis,
                    ),
                )
                raw = getattr(response, "text", None)
                if not raw:
                    raise ValueError("Gemini returned an empty response.")
                return _parse_and_validate(raw)

            except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
                last_error = exc
                if attempt == 0:
                    prompt += (
                        "\n\nThe previous output did not pass validation. "
                        "Return corrected JSON that follows the supplied schema exactly. "
                        "Use null for unresolved owner/deadline fields and valid YYYY-MM-DD dates."
                    )
                    continue
                break

            except Exception as exc:
                message = str(exc).lower()
                if "429" in message or "quota" in message or "rate" in message:
                    raise ExtractionError(
                        "Gemini rate limit reached. Wait a little and try again."
                    ) from exc
                if (
                    "api key" in message
                    or "permission" in message
                    or "401" in message
                    or "403" in message
                ):
                    raise ExtractionError(
                        "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
                    ) from exc
                raise ExtractionError(
                    "Gemini request failed. Check your connection, model name, and API quota."
                ) from exc

        raise ExtractionError(
            "Gemini returned invalid structured output twice. Please try again."
        ) from last_error
    finally:
        client.close()


def analysis_to_dict(analysis: Analysis) -> dict[str, Any]:
    return analysis.model_dump(mode="json")
