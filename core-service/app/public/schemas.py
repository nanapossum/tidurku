from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PublicAggregateSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CityScoreAggregateOut(PublicAggregateSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "city": "Bandung",
                    "date": "2026-11-21",
                    "averageScore": 81.4,
                    "sampleSize": 8,
                }
            ]
        }
    )
    city: str
    date: date
    average_score: float
    sample_size: int


class DailyScoreAggregateOut(PublicAggregateSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "date": "2026-11-21",
                    "averageScore": 80.7,
                    "sampleSize": 12,
                }
            ]
        }
    )
    date: date
    average_score: float
    sample_size: int
