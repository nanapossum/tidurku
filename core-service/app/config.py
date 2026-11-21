from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "tidurku"
    database_url: str = "sqlite:////data/tidurku.db"
    jwt_secret: str = "ganti-ini"
    jwt_expire_minutes: int = 120
    # daftar API key kelompok lain, dipisah koma: kelompokA:key1,kelompokB:key2
    api_keys: str = ""


settings = Settings()
