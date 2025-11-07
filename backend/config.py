"""
Configuration management for Lumen Medical LLM
Supports multiple environments and secure secret handling
"""

import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_secret_key: str = Field(
        default="dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    )
    api_access_token_expire_minutes: int = Field(default=30)
    api_refresh_token_expire_days: int = Field(default=7)

    # Database
    database_url: str = Field(default="postgresql://localhost:5432/lumen_dev")
    database_pool_size: int = Field(default=5)
    database_max_overflow: int = Field(default=10)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = Field(default=3600)  # 1 hour

    # Vector Database (Qdrant)
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: Optional[str] = Field(default=None)
    qdrant_collection_name: str = Field(default="medical_knowledge")

    # Model Configuration
    model_name: str = Field(default="BioMistral-7B-DARE")
    model_path: str = Field(default="./model/checkpoints/lumen-medical-v1")
    inference_device: str = Field(default="cuda")
    inference_batch_size: int = Field(default=8)
    max_length: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)

    # RAG Configuration
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    retrieval_top_k: int = Field(default=5)
    rag_confidence_threshold: float = Field(default=0.7)

    # Training Configuration
    runpod_api_key: Optional[str] = Field(default=None)
    wandb_api_key: Optional[str] = Field(default=None)
    wandb_project: str = Field(default="lumen-medical-llm")
    wandb_entity: Optional[str] = Field(default=None)

    # Data Collection
    pubmed_api_key: Optional[str] = Field(default=None)
    pubmed_email: str = Field(default="research@lumen-medical.ai")
    fda_api_key: Optional[str] = Field(default=None)
    scraper_user_agent: str = Field(
        default="LumenMedicalBot/1.0 (+https://lumen-medical.ai/bot; research@lumen-medical.ai)"
    )
    scraper_delay: float = Field(default=1.0)
    scraper_max_retries: int = Field(default=3)

    # Storage
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_s3_bucket: str = Field(default="lumen-medical-data")
    aws_region: str = Field(default="us-east-1")

    # Cloudflare R2 (alternative to S3)
    r2_access_key_id: Optional[str] = Field(default=None)
    r2_secret_access_key: Optional[str] = Field(default=None)
    r2_bucket: str = Field(default="lumen-medical-data")
    r2_endpoint: Optional[str] = Field(default=None)

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None)
    log_level: str = Field(default="INFO")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)

    # HIPAA Compliance
    enable_audit_logging: bool = Field(default=True)
    data_retention_days: int = Field(default=2555)  # 7 years
    encryption_key: Optional[str] = Field(default=None)

    # Feature Flags
    enable_patient_features: bool = Field(default=True)
    enable_pharma_features: bool = Field(default=True)
    enable_student_features: bool = Field(default=False)
    enable_medical_imaging: bool = Field(default=False)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000")

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in v.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == Environment.PRODUCTION

    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    def get_storage_config(self) -> dict:
        """Get storage configuration (S3 or R2)"""
        if self.r2_access_key_id:
            return {
                "type": "r2",
                "access_key_id": self.r2_access_key_id,
                "secret_access_key": self.r2_secret_access_key,
                "bucket": self.r2_bucket,
                "endpoint": self.r2_endpoint,
            }
        return {
            "type": "s3",
            "access_key_id": self.aws_access_key_id,
            "secret_access_key": self.aws_secret_access_key,
            "bucket": self.aws_s3_bucket,
            "region": self.aws_region,
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use this function to access settings throughout the application
    """
    return Settings()


# Convenience exports
settings = get_settings()
