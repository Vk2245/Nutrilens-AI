"""
NutriLens Dashboard Router
============================
Purpose: Daily/weekly nutrition dashboard and meal logging endpoints.
Inputs:  User ID, meal data
Outputs: DailyLog summaries, weekly trends, logged meal confirmations
Deps:    FastAPI, firebase_service
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter
from models import MealEntry
from services.firebase_service import firebase_service
from services.fit_service import fit_service
from config import DEMO_USER_ID

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.dashboard")

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get(
    "/daily",
    summary="Get daily nutrition summary",
    description="Real-time daily nutrition overview with calories, macros, "
    "streak count, and meal list. Powered by Firebase Realtime Database.",
)
async def get_daily_summary(user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    """Get today's nutrition dashboard data."""
    daily_log = await firebase_service.get_daily_log(user_id)
    profile = await firebase_service.get_user_profile(user_id)
    activity = await fit_service.get_daily_activity()

    return {
        "daily_log": daily_log,
        "profile": {
            "name": profile.get("name", "User"),
            "calorie_goal": profile.get("daily_calorie_target", 2000),
            "dietary_goal": profile.get("dietary_goal", "general_wellness"),
        },
        "activity": activity,
        "calorie_goal_adjusted": profile.get("daily_calorie_target", 2000)
        + activity.get("calorie_adjustment", 0),
    }


@router.get(
    "/weekly",
    summary="Get weekly nutrition trends",
    description="7-day nutrition trends with daily totals and averages.",
)
async def get_weekly_trends(user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    """Get weekly nutrition trends for charts and habit analysis."""
    weekly_logs = await firebase_service.get_weekly_logs(user_id)

    days_with_data = [d for d in weekly_logs if d.get("total_calories", 0) > 0]
    avg_calories = (
        sum(d.get("total_calories", 0) for d in days_with_data) / len(days_with_data)
        if days_with_data
        else 0
    )

    return {
        "weekly_logs": weekly_logs,
        "summary": {
            "avg_daily_calories": round(avg_calories),
            "days_logged": len(days_with_data),
            "total_meals": sum(len(d.get("meals", [])) for d in weekly_logs),
        },
    }


@router.post(
    "/log-meal",
    summary="Log a meal manually",
    description="Manually log a meal entry to Firebase RTDB and update daily totals.",
)
async def log_meal_manual(meal: MealEntry, user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    """Log a meal entry and return updated daily summary."""
    meal_data = meal.model_dump()
    updated_log = await firebase_service.log_meal(user_id, meal_data)
    return {"status": "logged", "daily_log": updated_log}
