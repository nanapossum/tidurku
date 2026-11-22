import re

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class ReminderSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class ReminderOut(ReminderSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"enabled": True, "time": "22:30", "isCustom": False}]
        }
    )
    enabled: bool
    time: str
    is_custom: bool


class ReminderUpdateIn(ReminderSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"enabled": True, "time": "22:30"}]
        }
    )
    enabled: bool
    time: str | None = None

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is not None and re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d",
            value,
        ) is None:
            raise ValueError("Waktu pengingat harus menggunakan format HH:MM.")
        return value
