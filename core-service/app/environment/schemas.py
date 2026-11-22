from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class EnvironmentSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class EnvironmentFindingOut(EnvironmentSchema):
    factor: Literal["temperature", "caffeine", "screen"]
    correlation: float | None
    direction: Literal["negatif", "positif", "netral"]
    message: str


class EnvironmentInsightOut(EnvironmentSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "available": True,
                    "sampleSize": 10,
                    "minRequired": 7,
                    "temperatureAvailable": True,
                    "findings": [
                        {
                            "factor": "temperature",
                            "correlation": 0.35,
                            "direction": "positif",
                            "message": "Kecenderungan positif teramati.",
                        }
                    ],
                    "disclaimer": "Hasil ini hanya menggambarkan korelasi.",
                }
            ]
        }
    )
    available: bool
    sample_size: int
    min_required: int = 7
    temperature_available: bool
    findings: list[EnvironmentFindingOut]
    disclaimer: str
