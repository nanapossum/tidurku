from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)
from pydantic.alias_generators import to_camel


StressLevel = Literal["Rendah", "Sedang", "Tinggi"]


class TrackingSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class SleepSessionIn(TrackingSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "startAt": "2026-11-20T22:30:00+07:00",
                    "endAt": "2026-11-21T06:30:00+07:00",
                    "quality": 4,
                    "stress": "Sedang",
                    "caffeine": 1,
                    "screenMinutes": 45,
                    "notes": "Minum kopi sore.",
                }
            ]
        }
    )
    start_at: AwareDatetime
    end_at: AwareDatetime
    quality: int | None = Field(default=None, ge=1, le=5)
    stress: StressLevel | None = None
    caffeine: int | None = Field(
        default=None,
        ge=0,
        le=9999,
        description="Jumlah shots kafein yang dicatat UI.",
    )
    screen_minutes: int | None = Field(default=None, ge=0, le=9999)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("stress", mode="before")
    @classmethod
    def empty_stress_is_missing(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("notes", mode="before")
    @classmethod
    def trim_notes(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SleepSessionOut(TrackingSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "c0a80101-0000-4000-8000-000000000002",
                    "userId": "c0a80101-0000-4000-8000-000000000001",
                    "startAt": "2026-11-20T15:30:00Z",
                    "endAt": "2026-11-20T23:30:00Z",
                    "quality": 4,
                    "stress": "Sedang",
                    "caffeine": 1,
                    "screenMinutes": 45,
                    "notes": "Minum kopi sore.",
                    "createdAt": "2026-11-21T01:00:00Z",
                    "updatedAt": "2026-11-21T01:00:00Z",
                    "score": 82,
                    "durationMinutes": 480,
                }
            ]
        }
    )
    id: str
    user_id: str
    start_at: AwareDatetime
    end_at: AwareDatetime
    quality: int | None
    stress: StressLevel | None
    caffeine: int | None
    screen_minutes: int | None
    notes: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    score: int | None = None

    @computed_field
    @property
    def duration_minutes(self) -> int:
        seconds = (self.end_at - self.start_at).total_seconds()
        return int(seconds / 60 + 0.5)


class SleepSessionListOut(TrackingSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": "c0a80101-0000-4000-8000-000000000002",
                            "userId": "c0a80101-0000-4000-8000-000000000001",
                            "startAt": "2026-11-20T15:30:00Z",
                            "endAt": "2026-11-20T23:30:00Z",
                            "quality": 4,
                            "stress": "Sedang",
                            "caffeine": 1,
                            "screenMinutes": 45,
                            "notes": None,
                            "createdAt": "2026-11-21T01:00:00Z",
                            "updatedAt": "2026-11-21T01:00:00Z",
                            "score": 82,
                            "durationMinutes": 480,
                        }
                    ],
                    "total": 1,
                    "limit": 30,
                    "offset": 0,
                }
            ]
        }
    )
    items: list[SleepSessionOut]
    total: int
    limit: int
    offset: int


