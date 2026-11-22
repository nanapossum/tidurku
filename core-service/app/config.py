from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    service_name: str = "tidurku"
    database_url: str = "sqlite:////data/tidurku.db"
    jwt_secret: str
    jwt_expire_minutes: int = 120
    api_keys: str = ""
    timezone: str = "Asia/Jakarta"
    jwt_algorithm: str = "HS256"
    aggregate_min_users: int = 5

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET wajib diisi.")
        if len(value) < 32:
            raise ValueError("JWT_SECRET harus memiliki minimal 32 karakter.")
        if "GANTI" in value.upper():
            raise ValueError("JWT_SECRET tidak boleh mengandung kata GANTI.")
        return value


settings = Settings()


def parse_api_keys() -> dict[str, str]:
    """Parse API_KEYS dalam format nama:key,nama2:key2."""
    parsed: dict[str, str] = {}
    for entry in settings.api_keys.split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, separator, key = entry.partition(":")
        name, key = name.strip(), key.strip()
        if not separator or not name or not key:
            raise ValueError("API_KEYS harus memakai format nama:key.")
        parsed[name] = key
    return parsed
