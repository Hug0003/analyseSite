"""
Configuration settings for SiteAuditor Backend
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Google PageSpeed API
    google_pagespeed_api_key: str = ""
    wappalyzer_api_key: str = ""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./siteauditor.db"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    
    # Request Timeouts (seconds)
    request_timeout: int = 30
    ssl_timeout: int = 10
    
    # JWT Configuration
    secret_key: str = "your-secret-key-CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Mail Configuration
    mail_username: str = "user@example.com"
    mail_password: str = ""
    mail_from: str = "noreply@siteauditor.com"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    
    # AI Configuration
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
