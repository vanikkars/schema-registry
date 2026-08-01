"""Configuration."""

import os


class Settings:
    """Service settings."""
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    aws_glue_database: str = os.getenv("ICEBERG_AWS_GLUE_DATABASE", "iceberg_tables")
    s3_bucket_prefix: str = os.getenv("ICEBERG_S3_BUCKET_PREFIX", "iceberg-data")