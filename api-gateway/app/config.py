"""Application configuration and settings loading for the API Gateway."""
import os
from dataclasses import dataclass
from typing import Type


@dataclass
class BaseConfig:
    app_env: str = "development"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    users_service_url: str = os.getenv("USERS_SERVICE_URL", "http://users-service:5001")
    management_service_url: str = os.getenv(
        "MANAGEMENT_SERVICE_URL", "http://management-service:5002"
    )
    financial_service_url: str = os.getenv(
        "FINANCIAL_SERVICE_URL", "http://financial-service:5003"
    )
    teamcrm_service_url: str = os.getenv(
        "TEAMCRM_SERVICE_URL", "http://teamcrm-service:5004"
    )
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://ai-service:5005")
    frontend_dist_path: str = os.getenv("FRONTEND_DIST_PATH", "/app/frontend/dist")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class ProductionConfig(BaseConfig):
    app_env: str = "production"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class DevelopmentConfig(BaseConfig):
    app_env: str = "development"
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")


CONFIG_MAP: dict[str, Type[BaseConfig]] = {
    "production": ProductionConfig,
    "development": DevelopmentConfig,
    "staging": ProductionConfig,
}


def load_config() -> BaseConfig:
    env = os.getenv("APP_ENV", "development").lower()
    config_class = CONFIG_MAP.get(env, DevelopmentConfig)
    return config_class()
