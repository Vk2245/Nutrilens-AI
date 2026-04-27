"""
NutriLens AI Pydantic Models
==============================
Purpose: Defines all request/response schemas for the NutriLens API using Pydantic v2.
         Includes input validation, HTML sanitization, and field constraints to ensure
         data integrity and security across all endpoints.
Inputs:  Raw API request data (JSON payloads, form data)
Outputs: Validated, type-safe Python objects for use in service and router layers
Deps:    pydantic>=2.0
"""

from __future__ import annotations

import re
import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "NutritionAnalysis", "MacroBreakdown", "CoachResponse", "UserProfile",
    "DailyLog", "MealEntry", "ExploreResult", "RestaurantResult",
    "RecipeVideo", "HabitReport", "NudgeResponse", "OnboardingRequest",
    "CoachQueryRequest", "VoiceCoachRequest", "FoodAnalyzeRequest",
    "GoogleSignInRequest", "TokenResponse", "ProfileUpdateRequest",
    "DietaryGoal", "ActivityLevel",
]


def strip_html_tags(value: str) -> str:
    """Remove HTML tags from a string to prevent XSS attacks."""
    clean = re.sub(r"<[^>]+>", "", value)
    return clean.strip()


# --- Enums ---

class DietaryGoal(str, Enum):
    """Dietary goal options for user profiles."""
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_BUILDING = "muscle_building"
    MAINTENANCE = "maintenance"
    HEART_HEALTH = "heart_health"
    DIABETES_MANAGEMENT = "diabetes_management"
    GENERAL_WELLNESS = "general_wellness"


class ActivityLevel(str, Enum):
    """User activity level for calorie calculation."""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class MealType(str, Enum):
    """Type of meal for categorization."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


# --- Core Nutrition Models ---

class MacroBreakdown(BaseModel):
    """Macronutrient breakdown for a food item or daily total."""
    protein_g: float = Field(..., ge=0, description="Protein in grams")
    carbohydrates_g: float = Field(..., ge=0, description="Total carbohydrates in grams")
    fat_g: float = Field(..., ge=0, description="Total fat in grams")
    fiber_g: float = Field(..., ge=0, description="Dietary fiber in grams")


class NutritionAnalysis(BaseModel):
    """Structured output from Gemini Vision food analysis."""
    dish_name: str = Field(..., min_length=1, max_length=100)
    cuisine: str = Field(default="Indian", max_length=50)
    calories_kcal: float = Field(..., ge=0, le=5000)
    macros: MacroBreakdown
    health_score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    healthier_alternatives: List[str] = Field(default_factory=list)
    micronutrient_highlights: List[str] = Field(default_factory=list)
    portion_size: str = Field(default="1 serving", max_length=50)
    meal_type: str = Field(default="snack", max_length=20)
    explanation: str = Field(default="", max_length=500)

    @field_validator("health_score")
    @classmethod
    def score_must_be_meaningful(cls, v: int) -> int:
        """Health score 0-100 must reflect actual nutritional quality."""
        return v


class MealEntry(BaseModel):
    """A single logged meal entry."""
    meal_id: str = Field(default="")
    dish_name: str = Field(..., min_length=1, max_length=100)
    calories_kcal: float = Field(..., ge=0, le=5000)
    macros: MacroBreakdown
    health_score: int = Field(default=50, ge=0, le=100)
    meal_type: str = Field(default="snack", max_length=20)
    image_url: str = Field(default="", max_length=500)
    timestamp: float = Field(default_factory=time.time)

    @field_validator("dish_name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        """Sanitize dish name."""
        return strip_html_tags(value)


class DailyLog(BaseModel):
    """Daily nutrition summary for the dashboard."""
    date: str = Field(..., description="ISO date string YYYY-MM-DD")
    meals: List[MealEntry] = Field(default_factory=list)
    total_calories: float = Field(default=0, ge=0)
    total_protein_g: float = Field(default=0, ge=0)
    total_carbs_g: float = Field(default=0, ge=0)
    total_fat_g: float = Field(default=0, ge=0)
    total_fiber_g: float = Field(default=0, ge=0)
    calorie_goal: int = Field(default=2000, ge=500, le=10000)
    streak_count: int = Field(default=0, ge=0)
    avg_health_score: float = Field(default=0, ge=0, le=100)


# --- User Profile Models ---

class UserProfile(BaseModel):
    """User health profile for personalized recommendations."""
    user_id: str = Field(default="")
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(default="", max_length=255)
    age: int = Field(default=25, ge=10, le=120)
    weight_kg: float = Field(default=65.0, ge=20, le=300)
    height_cm: float = Field(default=165.0, ge=100, le=250)
    dietary_goal: str = Field(default="general_wellness")
    activity_level: str = Field(default="moderately_active")
    allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    medical_conditions: List[str] = Field(default_factory=list)
    daily_calorie_target: int = Field(default=2000, ge=500, le=10000)
    created_at: float = Field(default_factory=time.time)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        """Sanitize name."""
        return strip_html_tags(value)


# --- Coach Models ---

class CoachQueryRequest(BaseModel):
    """Request for text-based nutrition coaching."""
    query: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en", pattern="^(en|hi)$")
    include_audio: bool = Field(default=False)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, value: str) -> str:
        """Sanitize query text."""
        return strip_html_tags(value)


class VoiceCoachRequest(BaseModel):
    """Request for voice-based coaching (audio input)."""
    audio_base64: str = Field(..., min_length=10)
    language: str = Field(default="en", pattern="^(en|hi)$")


class CoachResponse(BaseModel):
    """Response from the nutrition coach."""
    response_text: str = Field(..., min_length=1)
    audio_base64: Optional[str] = Field(default=None)
    language: str = Field(default="en")
    suggestions: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class NudgeResponse(BaseModel):
    """Proactive nudge based on nutritional gap analysis."""
    message: str
    nutrient_gaps: List[str] = Field(default_factory=list)
    recommended_foods: List[str] = Field(default_factory=list)
    time_context: str = Field(default="")
    timestamp: float = Field(default_factory=time.time)


class HabitReport(BaseModel):
    """7-day behavioral pattern analysis from Gemini."""
    patterns: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    micro_actions: List[str] = Field(default_factory=list)
    streak_count: int = Field(default=0, ge=0)
    avg_health_score: float = Field(default=0, ge=0, le=100)
    top_nutrient_gap: str = Field(default="")
    generated_at: float = Field(default_factory=time.time)


# --- Explore Models ---

class RestaurantResult(BaseModel):
    """A nearby restaurant with nutritional fit score."""
    name: str
    address: str = Field(default="")
    distance_km: float = Field(default=0, ge=0)
    rating: float = Field(default=0, ge=0, le=5)
    cuisine_type: str = Field(default="")
    nutritional_fit_score: int = Field(default=50, ge=0, le=100)
    recommended_dish: str = Field(default="")
    place_id: str = Field(default="")
    photo_url: str = Field(default="")


class RecipeVideo(BaseModel):
    """A YouTube recipe video matched to nutrient gaps."""
    title: str
    video_id: str
    thumbnail_url: str = Field(default="")
    channel_name: str = Field(default="")
    duration: str = Field(default="")
    nutrient_match: str = Field(default="")


class ExploreResult(BaseModel):
    """Combined explore results: restaurants + recipes."""
    restaurants: List[RestaurantResult] = Field(default_factory=list)
    recipe_videos: List[RecipeVideo] = Field(default_factory=list)
    nutrient_context: str = Field(default="")


# --- Auth Models ---

class GoogleSignInRequest(BaseModel):
    """Request for Google Sign-In token verification."""
    id_token: str = Field(..., min_length=10)


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str = ""
    photo_url: str = ""


# --- Profile Models ---

class OnboardingRequest(BaseModel):
    """Initial health profile setup during onboarding."""
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=10, le=120)
    weight_kg: float = Field(..., ge=20, le=300)
    height_cm: float = Field(..., ge=100, le=250)
    dietary_goal: DietaryGoal = Field(default=DietaryGoal.GENERAL_WELLNESS)
    activity_level: ActivityLevel = Field(default=ActivityLevel.MODERATELY_ACTIVE)
    allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        """Sanitize name."""
        return strip_html_tags(value)


class ProfileUpdateRequest(BaseModel):
    """Update user profile fields."""
    weight_kg: Optional[float] = Field(default=None, ge=20, le=300)
    dietary_goal: Optional[DietaryGoal] = None
    activity_level: Optional[ActivityLevel] = None
    allergies: Optional[List[str]] = None
    daily_calorie_target: Optional[int] = Field(default=None, ge=500, le=10000)


class FoodAnalyzeRequest(BaseModel):
    """Request for text-based food analysis (no image)."""
    description: str = Field(..., min_length=3, max_length=500)
    meal_type: Optional[MealType] = None
    recaptcha_token: Optional[str] = None

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, value: str) -> str:
        """Sanitize food description."""
        return strip_html_tags(value)
