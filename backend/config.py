"""
Configuration management for FOAM Grant Alignment Engine.

Handles environment-based configuration using Pydantic Settings.
Supports dev, staging, and production environments.
"""

import json
from typing import Optional, Any
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


def _parse_list_field(v: Any) -> list[str]:
    """Parse a value that should be a list of strings.

    Handles: JSON arrays, comma-separated strings, or already-parsed lists.
    """
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        v = v.strip()
        # Try JSON parse first (e.g. '["a","b"]')
        if v.startswith("["):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to comma-separated
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    # Application Metadata
    APP_NAME: str = "FOAM Grant Alignment Engine API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered grant alignment and compliance analysis for Fathers On A Mission"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/foam_grants",
        description="Async PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after this many seconds")
    DATABASE_ECHO: bool = Field(default=False, description="Log all SQL statements")

    # API Configuration
    API_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = Field(default=8000, ge=1024, le=65535)

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # File Upload Configuration
    UPLOAD_DIR: str = "/tmp/foam_uploads"
    UPLOAD_MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="Max file size in bytes (50MB)")
    ALLOWED_FILE_TYPES: list[str] = [".pdf", ".docx", ".doc", ".txt"]

    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"

    # AWS S3 Configuration (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_REGION: str = "us-east-1"

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = "json"  # json or text

    # FOAM Organization Data
    ORGANIZATION_NAME: str = "Fathers On A Mission"
    ORGANIZATION_EIN: str = "82-2374110"
    ORGANIZATION_501C3: bool = True
    ORGANIZATION_FOUNDED: int = 2017
    ORGANIZATION_LOCATION: str = "East Baton Rouge Parish, Louisiana"

    # FOAM Program Configuration
    FOAM_ANNUAL_TARGET_FATHERS: int = 140
    FOAM_ANNUAL_TARGET_CHILDREN: int = 210
    FOAM_PROGRAMS: list[str] = [
        "Project Family Build",
        "Responsible Fatherhood Classes",
        "Celebration of Fatherhood Events",
        "Louisiana Barracks Program"
    ]

    # Data System Integration
    EMPOWERDB_ENABLED: bool = False
    EMPOWERDB_API_URL: Optional[str] = None
    NFORM_ENABLED: bool = False
    NFORM_API_URL: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @model_validator(mode="before")
    @classmethod
    def pre_process_list_fields(cls, values: dict) -> dict:
        """Pre-process list fields from environment variable strings.

        pydantic-settings parses env vars before field validators run,
        so we must use model_validator(mode='before') to handle
        comma-separated strings for list fields.
        """
        list_fields = [
            "CORS_ORIGINS",
            "CORS_ALLOW_METHODS",
            "CORS_ALLOW_HEADERS",
            "ALLOWED_FILE_TYPES",
            "FOAM_PROGRAMS",
        ]
        for field_name in list_fields:
            if field_name in values and isinstance(values[field_name], str):
                values[field_name] = _parse_list_field(values[field_name])

        # Fix DATABASE_URL: convert postgres:// to postgresql+asyncpg://
        db_url = values.get("DATABASE_URL", "")
        if isinstance(db_url, str):
            if db_url.startswith("postgres://"):
                values["DATABASE_URL"] = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://") and "asyncpg" not in db_url:
                values["DATABASE_URL"] = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return values

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    def get_database_url(self) -> str:
        """Get the database URL."""
        return self.DATABASE_URL


# Global settings instance
settings = Settings()
