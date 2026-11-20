import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from extractor import ExtractionError, _build_prompt, extract_analysis
from schemas import Analysis


VALID = {
    "summary": "A planning meeting.",
    "key_points": ["Riya owns the report."],
    "action_items": [{
        "task": "Prepare report",
        "owner": "Riya",
        "deadline": "2026-11-27",
        "priority": "medium",
        "evidence": "Riya will prepare the report by next Friday.",
    }],
    "key_dates": [],
}


def test_prompt_uses_document_date_and_source_only_rules():
    prompt = _build_prompt(
        "Riya will prepare the report by next Friday.",
        date(2026, 11, 20),
    )
    assert "2026-11-20" in prompt
    assert "verbatim" in prompt.lower()
    assert "null" in prompt.lower()


@patch("extractor.genai.Client")
def test_extractor_validates_schema_constrained_output(mock_client_class):
    response = MagicMock()
    response.text = json.dumps(VALID)
    client = mock_client_class.return_value
    client.models.generate_content.return_value = response

    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "gemini-2.5-flash",
    }):
        result = extract_analysis(
            "Riya will prepare the report by next Friday.",
            date(2026, 11, 20),
        )

    assert result.action_items[0].owner == "Riya"
    call = client.models.generate_content.call_args.kwargs
    assert call["model"] == "gemini-2.5-flash"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is Analysis
    client.close.assert_called_once()


@patch("extractor.genai.Client")
def test_extractor_retries_malformed_response_once(mock_client_class):
    bad, good = MagicMock(), MagicMock()
    bad.text, good.text = "not json", json.dumps(VALID)
    client = mock_client_class.return_value
    client.models.generate_content.side_effect = [bad, good]

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        result = extract_analysis(
            "Riya will prepare the report.",
            date(2026, 11, 20),
        )

    assert result.summary == VALID["summary"]
    assert client.models.generate_content.call_count == 2
    client.close.assert_called_once()


@patch("extractor.genai.Client")
def test_extractor_returns_friendly_error_after_second_invalid_response(mock_client_class):
    invalid = MagicMock()
    invalid.text = "not json"
    client = mock_client_class.return_value
    client.models.generate_content.return_value = invalid

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with pytest.raises(ExtractionError, match="invalid structured output"):
            extract_analysis(
                "Riya will prepare the report.",
                date(2026, 11, 20),
            )

    assert client.models.generate_content.call_count == 2
    client.close.assert_called_once()


def test_missing_api_key_has_friendly_error():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ExtractionError, match="GEMINI_API_KEY is missing"):
            extract_analysis("Some document text.", date(2026, 11, 20))
