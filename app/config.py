from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEBUG: bool = False
    APP_DB_PATH: str = "app.db"
    APP_DB_URL: str = ""
    JWT_SECRET: str = "dev-secret"
    JWT_TTL_MINUTES: int = 15
    RUNTIME_ADAPTER: str = "fake"
    CONTAINERD_SOCKET: str = "/run/containerd/containerd.sock"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Password123!"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    @model_validator(mode="after")
    def _prod_secret(self):
        if not self.DEBUG:
            if self.JWT_SECRET == "dev-secret":
                raise ValueError("JWT_SECRET must be set when DEBUG=false")
            if self.ADMIN_PASSWORD == "Password123!":
                raise ValueError("ADMIN_PASSWORD must be changed when DEBUG=false")
        return self


# settings = Settings()
