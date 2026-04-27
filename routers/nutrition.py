"""
NutriLens Nutrition Router
============================
Purpose: API endpoints for food image/text analysis using Gemini Vision.
Inputs:  Food images (multipart), text descriptions, reCAPTCHA tokens
Outputs: NutritionAnalysis structured responses with health scores
Deps:    FastAPI, gemini_service, firebase_service
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from models import FoodAnalyzeRequest, NutritionAnalysis
from services.gemini_service import gemini_service
from services.firebase_service import firebase_service
from services.sheets_service import sheets_service
from config import MAX_IMAGE_SIZE, ALLOWED_MIME_TYPES, DEMO_USER_ID

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.nutrition")

router = APIRouter(prefix="/api/v1/nutrition", tags=["Nutrition Analysis"])


@router.post(
    "/analyze",
    response_model=NutritionAnalysis,
    summary="Analyze food image with Gemini Vision",
    description="Upload a food photo for AI-powered nutritional analysis. "
    "Returns structured data: macros, health score, alternatives.",
)
async def analyze_food_image(
    image: UploadFile = File(..., description="Food photo (JPEG/PNG/WebP, max 10MB)"),
    user_id: str = Form(default=DEMO_USER_ID),
    meal_type: str = Form(default="snack"),
) -> NutritionAnalysis:
    """Analyze a food image using Gemini 2.0 Flash Vision.

    Accepts a food photo, validates the file type and size, sends to Gemini
    for multimodal analysis, and returns structured nutritional data.
    Results are cached by SHA-256 hash to avoid duplicate API calls.

    Args:
        image: Uploaded food photo (JPEG, PNG, or WebP).
        user_id: Authenticated user ID for personalized context.
        meal_type: Type of meal (breakfast/lunch/dinner/snack).

    Returns:
        NutritionAnalysis with macros, health score, and alternatives.

    Raises:
        HTTPException: 400 if image is invalid, 413 if too large.
    """
    # Validate MIME type
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {image.content_type}. Accepted: JPEG, PNG, WebP.",
        )

    # Read and validate size
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large. Maximum 10MB.")

    if len(image_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Image too small or corrupted.")

    # Get user context for personalized analysis
    profile = await firebase_service.get_user_profile(user_id)
    daily_log = await firebase_service.get_daily_log(user_id)
    user_context = {
        "dietary_goal": profile.get("dietary_goal", "general_wellness"),
        "allergies": profile.get("allergies", []),
        "calories_today": daily_log.get("total_calories", 0),
    }

    # Analyze with Gemini Vision
    result = await gemini_service.analyze_food_image(image_bytes, user_context)

    # Log the meal to Firebase RTDB
    meal_data = {
        "dish_name": result.dish_name,
        "calories_kcal": result.calories_kcal,
        "macros": result.macros.model_dump(),
        "health_score": result.health_score,
        "meal_type": meal_type,
    }
    await firebase_service.log_meal(user_id, meal_data)

    # Export to Google Sheets (async, non-blocking)
    await sheets_service.export_meal(user_id, meal_data)

    return result


@router.post(
    "/analyze-text",
    response_model=NutritionAnalysis,
    summary="Analyze food from text description",
    description="Describe what you ate in text and get AI nutritional analysis.",
)
async def analyze_food_text(request: FoodAnalyzeRequest) -> NutritionAnalysis:
    """Analyze food from a text description using Gemini.

    Args:
        request: FoodAnalyzeRequest with description and optional meal_type.

    Returns:
        NutritionAnalysis with estimated macros and health score.
    """
    result = await gemini_service.analyze_food_text(request.description)
    return result


@router.get(
    "/history",
    summary="Get meal history",
    description="Retrieve logged meals for the current day.",
)
async def get_meal_history(user_id: str = DEMO_USER_ID):
    """Get today's meal history from Firebase RTDB.

    Args:
        user_id: User identifier.

    Returns:
        Daily log with all meals and totals.
    """
    return await firebase_service.get_daily_log(user_id)
