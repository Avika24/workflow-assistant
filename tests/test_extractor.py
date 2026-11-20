import json
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
from extractor import ExtractionError, _build_prompt, extract_analysis

VALID = {
    "summary": "A planning meeting.",
    "key_points": ["Riya owns the report."],
    "action_items": [{"task": "Prepare report", "owner": "Riya", "deadline": "2026-11-27",
                      "priority": "medium", "evidence": "Riya will prepare the report by next Friday."}],
    "key_dates": [],
}

@patch("extractor.genai.GenerativeModel")
@patch("extractor.genai.configure")
def test_extractor_validates_output_and_uses_document_date(mock_configure, mock_model):
    prompt = _build_prompt("Riya will prepare the report by next Friday.", date(2026, 11, 20))
    assert "2026-11-20" in prompt and "verbatim" in prompt.lower()
    response = MagicMock()
    response.text = json.dumps(VALID)
    mock_model.return_value.generate_content.return_value = response
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-2.5-flash"}):
        result = extract_analysis("Riya will prepare the report by next Friday.", date(2026, 11, 20))
    assert result.action_items[0].owner == "Riya"

@patch("extractor.genai.GenerativeModel")
@patch("extractor.genai.configure")
def test_extractor_retries_malformed_response_once(mock_configure, mock_model):
    bad, good = MagicMock(), MagicMock()
    bad.text, good.text = "not json", json.dumps(VALID)
    mock_model.return_value.generate_content.side_effect = [bad, good]
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        result = extract_analysis("Riya will prepare the report.", date(2026, 11, 20))
    assert result.summary == VALID["summary"]
    assert mock_model.return_value.generate_content.call_count == 2

@patch("extractor.genai.GenerativeModel")
@patch("extractor.genai.configure")
def test_extractor_returns_friendly_error_after_second_invalid_response(mock_configure, mock_model):
    invalid = MagicMock()
    invalid.text = "not json"
    mock_model.return_value.generate_content.return_value = invalid
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with pytest.raises(ExtractionError, match="invalid structured output"):
            extract_analysis("Riya will prepare the report.", date(2026, 11, 20))
    assert mock_model.return_value.generate_content.call_count == 2
