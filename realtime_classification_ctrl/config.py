from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    keycloak_url: str = Field(default="https://dev1.m4d.iti.gr/koban/auth", validation_alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="koban", validation_alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="koban-backend-services", validation_alias="KEYCLOAK_CLIENT_ID")

    realtime_bullying_api_url: str | None = Field(default=None, validation_alias="REALTIME_BULLYING_API_URL")
    realtime_bullying_ocr_api_url: str | None = Field(default=None, validation_alias="REALTIME_BULLYING_OCR_API_URL")


settings = Settings()

# Keycloak Endpoints
KEYCLOAK_REALM_URL = f"{settings.keycloak_url.rstrip('/')}/realms/{settings.keycloak_realm}"
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_REALM_URL}/protocol/openid-connect/certs"
KEYCLOAK_ISSUER = KEYCLOAK_REALM_URL
KEYCLOAK_CLIENT_ID = settings.keycloak_client_id

REALTIME_BULLYING_API_URL = settings.realtime_bullying_api_url
REALTIME_BULLYING_OCR_API_URL = settings.realtime_bullying_ocr_api_url or settings.realtime_bullying_api_url
