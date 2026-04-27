"""
NutriLens Profile Router
==========================
Purpose: User profile management, onboarding, and health blueprint endpoints.
Inputs:  User profile data, dietary goals, health parameters
Outputs: Saved profiles, personalized health blueprints from Gemini
Deps:    FastAPI, firebase_service, gemini_service
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter
from models import OnboardingRequest, ProfileUpdateRequest
from services.firebase_service import firebase_service
from services.gemini_service import gemini_service
from config import DEMO_USER_ID

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.profile")

router = APIRouter(prefix="/api/v1/profile", tags=["Profile & Blueprint"])


@router.post(
    "/onboarding",
    summary="Complete onboarding",
    description="Set up initial health profile during first-time onboarding.",
)
async def complete_onboarding(
    request: OnboardingRequest, user_id: str = DEMO_USER_ID
) -> Dict[str, Any]:
    """Save initial health profile and generate personalized calorie target."""
    # Calculate BMR using Mifflin-St Jeor
    bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age - 161
    activity_multipliers = {
        "sedentary": 1.2, "lightly_active": 1.375,
        "moderately_active": 1.55, "very_active": 1.725,
        "extremely_active": 1.9,
    }
    tdee = bmr * activity_multipliers.get(request.activity_level.value, 1.55)

    goal_adjustments = {
        "weight_loss": -500, "weight_gain": 300,
        "muscle_building": 200, "maintenance": 0,
    }
    calorie_target = int(tdee + goal_adjustments.get(request.dietary_goal.value, 0))

    profile = {
        "user_id": user_id,
        "name": request.name,
        "age": request.age,
        "weight_kg": request.weight_kg,
        "height_cm": request.height_cm,
        "dietary_goal": request.dietary_goal.value,
        "activity_level": request.activity_level.value,
        "allergies": request.allergies,
        "dietary_preferences": request.dietary_preferences,
        "daily_calorie_target": calorie_target,
    }
    await firebase_service.save_user_profile(user_id, profile)

    return {"status": "onboarding_complete", "profile": profile, "calorie_target": calorie_target}


@router.get(
    "/blueprint",
    summary="Get personalized health blueprint",
    description="Gemini generates a personalized nutrition blueprint based on "
    "your profile, goals, allergies, and activity level.",
)
async def get_health_blueprint(user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    """Generate a personalized health blueprint using Gemini."""
    profile = await firebase_service.get_user_profile(user_id)

    user_context = {
        "name": profile.get("name", "User"),
        "dietary_goal": profile.get("dietary_goal", "general_wellness"),
        "allergies": profile.get("allergies", []),
        "calories_today": 0,
        "calorie_goal": profile.get("daily_calorie_target", 2000),
        "protein_today": 0,
        "meals_count": 0,
    }

    response = await gemini_service.get_coach_response(
        "Create a personalized daily meal plan and nutrition blueprint for me. "
        "Include breakfast, lunch, dinner, and 2 snacks with specific Indian food suggestions.",
        user_context,
    )

    return {
        "profile": profile,
        "blueprint": response.response_text,
        "suggestions": response.suggestions,
    }


@router.put(
    "/goals",
    summary="Update dietary goals",
    description="Update dietary goals and recalculate calorie targets.",
)
async def update_goals(
    request: ProfileUpdateRequest, user_id: str = DEMO_USER_ID
) -> Dict[str, Any]:
    """Update user goals and recalculate targets."""
    profile = await firebase_service.get_user_profile(user_id)

    if request.weight_kg is not None:
        profile["weight_kg"] = request.weight_kg
    if request.dietary_goal is not None:
        profile["dietary_goal"] = request.dietary_goal.value
    if request.activity_level is not None:
        profile["activity_level"] = request.activity_level.value
    if request.allergies is not None:
        profile["allergies"] = request.allergies
    if request.daily_calorie_target is not None:
        profile["daily_calorie_target"] = request.daily_calorie_target

    await firebase_service.save_user_profile(user_id, profile)
    return {"status": "updated", "profile": profile}
