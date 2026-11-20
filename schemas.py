"""Pydantic schemas for validated DocFlow output."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator

class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: str
    owner: str | None = None
    deadline: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    evidence: str

    @field_validator("task", "evidence")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("owner")
    @classmethod
    def clean_owner(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value

class KeyDate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: str
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

class Analysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    key_points: list[str]
    action_items: list[ActionItem]
    key_dates: list[KeyDate]
