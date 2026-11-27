
"""Configuration de l'application, lue depuis les variables d'environnement / .env"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/bornes"

    # Origines autorisées à appeler l'API depuis un navigateur (CORS), séparées par des virgules.
    # Inutile quand l'interface passe par le proxy nginx (même origine) ; utile en développement
    # quand le front est servi sur un autre port (ex. http://localhost:5500).
    cors_origins: str = "http://localhost:8080,http://localhost:5500,http://127.0.0.1:5500"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
