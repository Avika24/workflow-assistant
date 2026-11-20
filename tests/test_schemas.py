from pydantic import ValidationError
import pytest

from schemas import ActionItem, Analysis


def test_valid_analysis_schema():
    result = Analysis.model_validate({
        "summary": "Weekly planning.",
        "key_points": ["Report due Friday."],
        "action_items": [{
            "task": "Prepare report",
            "owner": "Riya",
            "deadline": "2026-11-27",
            "priority": "high",
            "evidence": "Riya will prepare the report by Friday.",
        }],
        "key_dates": [{"event": "Review", "date": "2026-11-30"}],
    })
    assert result.action_items[0].deadline == "2026-11-27"


def test_invalid_deadline_rejected():
    with pytest.raises(ValidationError):
        ActionItem(task="Prepare report", deadline="next Friday", evidence="Prepare report")


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        Analysis.model_validate({
            "summary": "x", "key_points": [], "action_items": [],
            "key_dates": [], "extra": True,
        })
