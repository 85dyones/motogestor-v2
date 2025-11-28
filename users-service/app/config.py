"""Configuration object for the users-service with validation defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Type


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass
class BaseConfig:
    app_env: str = os.getenv("APP_ENV", "development")
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "dev-secret"))
    db_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "motogestor"))
    db_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "motogestor_pwd"))
    db_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "postgres"))
    db_name: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "motogestor_dev"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @property
    def database_url(self) -> str:
        return os.getenv(
            "DATABASE_URL",
            f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:5432/{self.db_name}",
        )


@dataclass
class ProductionConfig(BaseConfig):
    app_env: str = "production"
    jwt_secret_key: str = field(default_factory=lambda: _required("JWT_SECRET_KEY"))
    db_user: str = field(default_factory=lambda: _required("POSTGRES_USER"))
    db_password: str = field(default_factory=lambda: _required("POSTGRES_PASSWORD"))
    db_host: str = field(default_factory=lambda: _required("POSTGRES_HOST"))
    db_name: str = field(default_factory=lambda: _required("POSTGRES_DB"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


@dataclass
class DevelopmentConfig(BaseConfig):
    app_env: str = "development"
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "DEBUG"))


@dataclass
class TestingConfig(BaseConfig):
    app_env: str = "test"
    database_url: str = "sqlite:///:memory:"
    log_level: str = "DEBUG"


CONFIG_MAP: dict[str, Type[BaseConfig]] = {
    "production": ProductionConfig,
    "development": DevelopmentConfig,
    "staging": ProductionConfig,
    "test": TestingConfig,
}


def load_config() -> BaseConfig:
    env = os.getenv("APP_ENV", "development").lower()
    config_class = CONFIG_MAP.get(env, DevelopmentConfig)
    return config_class()
