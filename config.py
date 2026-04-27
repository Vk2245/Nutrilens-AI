"""
NutriLens AI Configuration Module
==================================
Purpose: Centralizes all application configuration, environment variable loading,
         and constants used throughout the NutriLens platform.
Inputs:  Environment variables from .env file (local) or container env (production)
Outputs: Singleton `settings` instance and application constants
Deps:    python-dotenv>=1.0.0
"""

from __future__ import annotations
import os
from typing import List
from dotenv import load_dotenv

__all__ = ["settings", "Settings"]

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        self.gemini_api_keys: List[str] = []
        if os.getenv("GEMINI_API_KEY_6104"):
            self.gemini_api_keys.append(os.getenv("GEMINI_API_KEY_6104"))
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_api_keys.append(os.getenv("GEMINI_API_KEY"))
        self.gemini_api_key: str = self.gemini_api_keys[0] if self.gemini_api_keys else ""

        self.google_credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        self.google_sheets_id: str = os.getenv("GOOGLE_SHEETS_ID", "")

        self.firebase_api_key: str = os.getenv("FIREBASE_API_KEY", "")
        self.firebase_auth_domain: str = os.getenv("FIREBASE_AUTH_DOMAIN", "")
        self.firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "nutrilensai")
        self.firebase_database_url: str = os.getenv("FIREBASE_DATABASE_URL", "https://nutrilensai-default-rtdb.firebaseio.com")
        self.firebase_storage_bucket: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")
        self.firebase_messaging_sender_id: str = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
        self.firebase_app_id: str = os.getenv("FIREBASE_APP_ID", "")
        self.firebase_measurement_id: str = os.getenv("FIREBASE_MEASUREMENT_ID", "")

        self.google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
        self.youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")

        self.recaptcha_site_key: str = os.getenv("RECAPTCHA_SITE_KEY", "")
        self.recaptcha_secret_key: str = os.getenv("RECAPTCHA_SECRET_KEY", "")

        self.app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret-key-change-in-production")
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


settings = Settings()

# Rate limiting
RATE_LIMIT_ANALYZE: int = 10
RATE_LIMIT_COACH: int = 15
RATE_LIMIT_WINDOW: int = 60

# Cache TTL
CACHE_TTL_GEMINI: int = 300
CACHE_TTL_MAPS: int = 600
CACHE_TTL_YOUTUBE: int = 3600

# Upload limits
MAX_IMAGE_SIZE: int = 10 * 1024 * 1024
ALLOWED_MIME_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

# Nutrition defaults
DEFAULT_DAILY_CALORIES: int = 2000
DEFAULT_PROTEIN_G: int = 50
DEFAULT_CARBS_G: int = 250
DEFAULT_FAT_G: int = 65
DEFAULT_FIBER_G: int = 25

# Language
SUPPORTED_LANGUAGES: List[str] = ["en", "hi"]
DEFAULT_LANGUAGE: str = "en"

# Demo
DEMO_USER_ID: str = "demo-user-nutrilens"
DEMO_USER_NAME: str = "Priya Sharma"
DEMO_USER_EMAIL: str = "priya@nutrilens.demo"
