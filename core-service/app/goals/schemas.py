import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class GoalSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class HealthyRangeOut(GoalSchema):
    min: int
    max: int


class GoalOut(GoalSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "targetHours": 8,
                    "bedtime": "23:00",
                    "healthyRange": {"min": 7, "max": 9},
                    "isDefault": True,
                }
            ]
        }
    )
    target_hours: float
    bedtime: str
    healthy_range: HealthyRangeOut
    is_default: bool


class GoalUpdateIn(GoalSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "targetHours": 8,
                    "bedtime": "22:30",
                    "confirmOutOfRange": False,
                }
            ]
        }
    )
    target_hours: Annotated[float, Field(ge=4, le=12)]
    bedtime: str
    confirm_out_of_range: bool = False

    @field_validator("bedtime")
    @classmethod
    def validate_bedtime(cls, value: str) -> str:
        if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) is None:
            raise ValueError("Jam tidur harus menggunakan format HH:MM.")
        return value
