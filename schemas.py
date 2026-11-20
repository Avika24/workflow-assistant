"""Pydantic schemas for validated DocFlow output."""
from datetime import date
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


def _validate_iso_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date must use YYYY-MM-DD format.")
    date.fromisoformat(value)
    return value


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
        return _validate_iso_date(value) if value is not None else None


class KeyDate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: str
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return _validate_iso_date(value)


class Analysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    key_points: list[str]
    action_items: list[ActionItem]
    key_dates: list[KeyDate]
