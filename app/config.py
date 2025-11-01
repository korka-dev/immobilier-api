from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    postgres_url: str
    access_token_expire_minutes: int = 1440
    secret_key: str
    algorithm: str = "HS256"
    cors_origin: str = "*"
    chunk_size: int = 1024 * 1024
    sendinblue_api_key: str

    @property
    def postgres_database_url(self):
        # nom utilisé par Alembic
        return self.postgres_url


def get_settings() -> Settings:
    return Settings()

settings = get_settings()
