from functools import lru_cache

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = Field(default="development", pattern="^(development|production|test)$")
    app_secret_key: SecretStr
    secret_encryption_key: SecretStr = SecretStr("")
    database_url: PostgresDsn
    redis_url: str = Field(pattern=r"^redis://")
    ollama_base_url: AnyHttpUrl
    initial_admin_email: str = ""
    initial_admin_password: SecretStr = SecretStr("")
    cors_origins: str = "http://localhost:5173"
    tool_sandbox_root: str = "/data/tools"
    http_allowed_hosts: str = ""
    http_timeout_seconds: int = Field(default=15, ge=1, le=60)
    http_max_response_bytes: int = Field(default=1_000_000, ge=1024, le=10_000_000)
    max_request_body_bytes: int = Field(default=2_000_000, ge=1024, le=20_000_000)
    plugin_runtime_mode: str = Field(default="docker_sandbox", pattern="^(in_process|docker_sandbox)$")
    plugin_docker_proxy_url: str = Field(default="http://docker-proxy:2375/v1.44", pattern=r"^http://docker-proxy:2375/v1\.44$")
    plugin_sandbox_image: str = Field(default="python:3.12-slim", pattern=r"^[a-z0-9][a-z0-9._/-]*:[a-z0-9._-]+$")
    plugin_sandbox_cpu_nano: int = Field(default=500_000_000, ge=10_000_000, le=2_000_000_000)
    plugin_sandbox_memory_bytes: int = Field(default=134_217_728, ge=16_777_216, le=1_073_741_824)
    plugin_sandbox_pids_limit: int = Field(default=64, ge=1, le=256)
    plugin_sandbox_timeout_seconds: int = Field(default=20, ge=1, le=120)
    instagram_processing_poll_seconds: int = Field(default=5, ge=1, le=60)
    instagram_processing_timeout_seconds: int = Field(default=600, ge=30, le=1800)
    instagram_app_id: str = ""
    instagram_app_secret: SecretStr = SecretStr("")
    instagram_access_token: SecretStr = SecretStr("")
    instagram_user_id: str = ""
    instagram_api_version: str = Field(default="v23.0", pattern=r"^v\d+\.\d+$")
    instagram_account_label: str = "Development Instagram"
    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    @property
    def allowed_http_hosts(self) -> set[str]:
        return {host.strip().lower() for host in self.http_allowed_hosts.split(",") if host.strip()}

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
