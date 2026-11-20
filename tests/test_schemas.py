from pydantic import ValidationError
import pytest
from schemas import ActionItem, Analysis

def test_schema_accepts_valid_data_and_rejects_invalid_dates_and_fields():
    result = Analysis.model_validate({
        "summary": "Weekly planning.", "key_points": ["Report due Friday."],
        "action_items": [{"task": "Prepare report", "owner": "Riya", "deadline": "2026-11-27",
                          "priority": "high", "evidence": "Riya will prepare the report by Friday."}],
        "key_dates": [{"event": "Review", "date": "2026-11-30"}],
    })
    assert result.action_items[0].deadline == "2026-11-27"
    for invalid_deadline in ("next Friday", "20261127", "2026-02-30"):
        with pytest.raises(ValidationError):
            ActionItem(task="Prepare report", deadline=invalid_deadline, evidence="Prepare report")
    with pytest.raises(ValidationError):
        Analysis.model_validate({"summary": "x", "key_points": [], "action_items": [],
                                 "key_dates": [], "unexpected": True})
