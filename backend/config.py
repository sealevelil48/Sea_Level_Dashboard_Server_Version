"""
Configuration management for Sea Level Monitoring System
"""
import os
from typing import List
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://username:password@localhost:5432/sealevel_monitoring"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Cache Configuration
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # External Services
    ims_forecast_url: str = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_sea.xml"
    
    # Performance Settings
    max_data_points: int = 10000
    request_timeout: int = 30
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Database connection string with proper error handling
def get_database_url():
    """Get database URL with validation"""
    db_url = settings.database_url
    
    if not db_url or db_url == "postgresql://username:password@localhost:5432/sealevel_monitoring":
        raise ValueError(
            "Database URL not configured. Please set DATABASE_URL environment variable."
        )
    
    return db_url

# Logging configuration
def setup_logging():
    """Setup logging configuration"""
    import logging
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)