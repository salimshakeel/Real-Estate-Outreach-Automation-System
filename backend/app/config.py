"""
Application Configuration
All sensitive data loaded from environment variables (.env file)
NEVER hardcode secrets here!
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in backend/ folder with these values.
    """
    
    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = "Real Estate Outreach API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # ============================================
    # SERVER
    # ============================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ============================================
    # DATABASE (Required)
    # ============================================
    DATABASE_URL: str  # postgresql+asyncpg://user@localhost:5432/dbname
    
    # ============================================
    # CORS - Frontend URLs allowed to access API
    # ============================================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://real-estate-outreach-frontend.onrender.com"
    
    # ============================================
    # SENDGRID - Email Service (Optional for demo)
    # ============================================
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    SENDGRID_FROM_NAME: str = "Real Estate Outreach"
    
    # Webhook security: shared secret appended to webhook URL as ?secret=VALUE
    # Generate with: openssl rand -hex 32
    # Set your SendGrid webhook URL to:
    #   https://your-domain.com/webhooks/sendgrid/events?secret=THIS_VALUE
    SENDGRID_WEBHOOK_SECRET: Optional[str] = None
    
    # Email warming: max emails sent per day (resets at UTC midnight).
    # Warmup schedule: Week 1 = 100, Week 2 = 250, Week 3 = 500, Week 4+ = 1000
    # Set to 0 for unlimited (only after domain is warmed).
    SENDGRID_DAILY_SEND_LIMIT: int = 100
    
    # ============================================
    # OPENAI - AI Classification (Optional for demo)
    # ============================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # ============================================
    # TWILIO - SMS (Step 3; same vendor as SendGrid)
    # ============================================
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    # E.164 format, e.g. +15551234567 (your Twilio phone number)
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # ============================================
    # CALENDLY - Meeting Scheduling (Optional for demo)
    # ============================================
    CALENDLY_API_TOKEN: Optional[str] = None
    CALENDLY_WEBHOOK_SECRET: Optional[str] = None
    
    # ============================================
    # SECURITY
    # ============================================
    SECRET_KEY: str = "change-this-in-production-use-strong-random-key"
    
    class Config:
        # Load from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields in .env
        extra = "ignore"
    
    # ============================================
    # COMPUTED PROPERTIES
    # ============================================
    
    @property
    def cors_origins_list(self) -> list:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV == "development"
    
    @property
    def sendgrid_configured(self) -> bool:
        """Check if SendGrid is configured"""
        return bool(self.SENDGRID_API_KEY and self.SENDGRID_FROM_EMAIL)

    @property
    def twilio_configured(self) -> bool:
        """Check if Twilio SMS is configured"""
        return bool(
            self.TWILIO_ACCOUNT_SID
            and self.TWILIO_AUTH_TOKEN
            and self.TWILIO_PHONE_NUMBER
        )
    
    @property
    def openai_configured(self) -> bool:
        """Check if OpenAI is configured"""
        return bool(self.OPENAI_API_KEY)
    
    @property
    def calendly_configured(self) -> bool:
        """Check if Calendly is configured"""
        return bool(self.CALENDLY_API_TOKEN)
    
    @property
    def webhook_secret_configured(self) -> bool:
        """True when the SendGrid webhook secret is set"""
        return bool(self.SENDGRID_WEBHOOK_SECRET)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reading .env file on every request.
    """
    return Settings()


# ============================================
# USAGE EXAMPLE
# ============================================
# from app.config import get_settings
# 
# settings = get_settings()
# print(settings.DATABASE_URL)
# print(settings.sendgrid_configured)
