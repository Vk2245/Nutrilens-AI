"""
NutriLens Auth Router
=======================
Purpose: Authentication endpoints using Firebase Authentication (Google Sign-In).
Inputs:  Firebase ID tokens from Google Sign-In
Outputs: Verified user data, JWT-like access tokens
Deps:    FastAPI, firebase-admin
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException
from models import GoogleSignInRequest, TokenResponse
from services.firebase_service import firebase_service
from config import settings, DEMO_USER_ID, DEMO_USER_NAME, DEMO_USER_EMAIL

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/google-signin",
    response_model=TokenResponse,
    summary="Google Sign-In verification",
    description="Verifies Firebase ID token from Google Sign-In and returns "
    "a session token with user profile data.",
)
async def google_signin(request: GoogleSignInRequest) -> TokenResponse:
    """Verify Google Sign-In token via Firebase Admin SDK."""
    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(request.id_token)
        user_id = decoded["uid"]
        name = decoded.get("name", "NutriLens User")
        email = decoded.get("email", "")
        photo = decoded.get("picture", "")

        # Ensure profile exists in RTDB
        profile = await firebase_service.get_user_profile(user_id)
        if not profile or profile.get("user_id") == DEMO_USER_ID:
            await firebase_service.save_user_profile(user_id, {
                "user_id": user_id,
                "name": name,
                "email": email,
                "age": 25,
                "weight_kg": 65,
                "height_cm": 165,
                "dietary_goal": "general_wellness",
                "activity_level": "moderately_active",
                "allergies": [],
                "dietary_preferences": [],
                "daily_calorie_target": 2000,
                "created_at": time.time(),
            })

        return TokenResponse(
            access_token=f"nl_{uuid.uuid4().hex}",
            user_id=user_id,
            name=name,
            email=email,
            photo_url=photo,
        )

    except ImportError:
        logger.warning("firebase-admin not available — demo signin")
        return TokenResponse(
            access_token=f"nl_demo_{uuid.uuid4().hex[:8]}",
            user_id=DEMO_USER_ID,
            name=DEMO_USER_NAME,
            email=DEMO_USER_EMAIL,
        )
    except Exception as e:
        logger.error("Google Sign-In failed: %s", str(e))
        # Fallback to demo mode for evaluators
        if settings.demo_mode:
            return TokenResponse(
                access_token=f"nl_demo_{uuid.uuid4().hex[:8]}",
                user_id=DEMO_USER_ID,
                name=DEMO_USER_NAME,
                email=DEMO_USER_EMAIL,
            )
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get(
    "/profile",
    summary="Get user profile",
    description="Retrieve the authenticated user's health profile.",
)
async def get_profile(user_id: str = DEMO_USER_ID):
    """Get user profile from Firebase RTDB."""
    return await firebase_service.get_user_profile(user_id)


@router.get(
    "/demo-login",
    response_model=TokenResponse,
    summary="Demo login for evaluators",
    description="Quick demo login — no Google account needed for evaluation.",
)
async def demo_login() -> TokenResponse:
    """Provide demo access for hackathon evaluators."""
    return TokenResponse(
        access_token=f"nl_demo_{uuid.uuid4().hex[:8]}",
        user_id=DEMO_USER_ID,
        name=DEMO_USER_NAME,
        email=DEMO_USER_EMAIL,
    )
