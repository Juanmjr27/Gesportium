from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str | None = None
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    totem_api_key: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
