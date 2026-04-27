"""NutriLens AI — Gemini-Powered Contextual Nutrition Intelligence Platform.

Main FastAPI application providing AI-powered food analysis, personalized nutrition
coaching, and behavioral pattern recognition. Built for the Google Prompt-a-thon
hackathon addressing the "healthier food choices" challenge.

Features:
    - Snap & Know: Gemini 2.0 Flash Vision food image analysis
    - AI Nutrition Coach: Bilingual voice + text coaching (en-IN + hi-IN)
    - Real-time Dashboard: Firebase RTDB-powered daily nutrition tracking
    - Smart Context Engine: Proactive nudges based on nutritional gaps
    - Explore: Google Maps restaurant discovery + YouTube recipe videos
    - Behavioral Pattern Engine: 7-day habit analysis with micro-actions

Google Services Integration (18 services — ALL FREE tier):
    - Google Gemini 2.0 Flash (Vision + Text) — via AI Studio free key
    - Google Cloud Speech-to-Text — bilingual voice input
    - Google Cloud Text-to-Speech — WaveNet-D voice responses
    - Google Maps Places API (New) — restaurant discovery
    - Google Fit REST API — activity tracking integration
    - YouTube Data API v3 — recipe video discovery
    - Google Translate API — UI localization (EN ↔ Hindi)
    - Google Sheets API (gspread) — meal log export
    - Firebase Auth (Google Sign-In) — authentication
    - Firebase Realtime Database — live data sync
    - Firebase Storage — meal photo storage
    - Firebase Cloud Messaging — push notifications
    - Firebase Remote Config — feature flags
    - Firebase Hosting — frontend deployment
    - Google Analytics 4 — usage tracking
    - Google reCAPTCHA v3 — bot protection
    - Google Fonts API (Inter) — typography
    - Google Cloud Run — backend hosting
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from routers import auth, coach, dashboard, explore, nutrition, profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("nutrilens")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown events."""
    logger.info("🥗 NutriLens AI starting up...")

    # Initialize Firebase Admin SDK
    from services.firebase_service import firebase_service
    firebase_service.initialize()

    # Initialize Google Sheets
    from services.sheets_service import sheets_service
    sheets_service.initialize()

    logger.info("Environment: %s", settings.app_env)
    logger.info("Demo Mode: %s", settings.demo_mode)
    logger.info("✅ NutriLens AI ready to serve requests")
    yield

    logger.info("👋 NutriLens AI shutting down...")


# --- FastAPI Application ---
app = FastAPI(
    title="NutriLens AI — Gemini-Powered Nutrition Intelligence",
    description=(
        "NutriLens addresses the Prompt-a-thon challenge of helping individuals "
        "make better food choices and build healthier eating habits by leveraging "
        "available data, user behavior, and contextual inputs. Powered by "
        "Gemini 2.0 Flash, Firebase, and 18 Google Services."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- Register Routers ---
app.include_router(auth.router)
app.include_router(nutrition.router)
app.include_router(coach.router)
app.include_router(dashboard.router)
app.include_router(explore.router)
app.include_router(profile.router)

# --- Static Files ---
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Root & Health Endpoints ---

@app.get(
    "/",
    summary="Serve NutriLens Frontend",
    description="Serves the NutriLens PWA frontend application.",
    include_in_schema=False,
)
async def root():
    """Serve the NutriLens frontend application."""
    response = FileResponse("static/app.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get(
    "/health",
    summary="Health Check",
    description="Returns application health status for Cloud Run health checks.",
    tags=["System"],
)
async def health_check():
    """Check application health status."""
    return {
        "status": "healthy",
        "service": "NutriLens AI",
        "version": "1.0.0",
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode,
    }


@app.get(
    "/api/config/frontend",
    summary="Get Frontend Configuration",
    description="Returns non-sensitive configuration for Firebase and reCAPTCHA.",
    tags=["System"],
)
async def get_frontend_config():
    """Get frontend configuration for Firebase initialization."""
    return {
        "firebase": {
            "apiKey": settings.firebase_api_key,
            "authDomain": settings.firebase_auth_domain,
            "projectId": settings.firebase_project_id,
            "databaseURL": settings.firebase_database_url,
            "storageBucket": settings.firebase_storage_bucket,
            "messagingSenderId": settings.firebase_messaging_sender_id,
            "appId": settings.firebase_app_id,
            "measurementId": settings.firebase_measurement_id,
        },
        "recaptcha": {"siteKey": settings.recaptcha_site_key},
        "maps": {"apiKey": settings.google_maps_api_key},
        "demo_mode": settings.demo_mode,
    }
