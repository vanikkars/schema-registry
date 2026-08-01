"""Configuration for Iceberg Creation Service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration."""

    aws_region: str = "us-east-1"
    aws_glue_database: str = "iceberg_tables"
    s3_bucket_prefix: str = "iceberg-data"
    service_port: int = 8001
    service_host: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        env_prefix = "ICEBERG_"