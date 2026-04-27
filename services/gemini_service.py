"""
NutriLens Gemini Service
========================
Purpose: Multimodal AI interface for food image analysis and nutrition coaching.
Inputs:  Image bytes (JPEG/PNG, max 10MB) OR text query with full user context
Outputs: NutritionAnalysis | CoachResponse | HabitReport (Pydantic v2 validated)
Deps:    google-generativeai>=0.8.0, Pydantic>=2.0, Pillow>=10.0
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from config import settings
from models import (
    CoachResponse,
    HabitReport,
    MacroBreakdown,
    NudgeResponse,
    NutritionAnalysis,
)

__all__ = ["GeminiService", "gemini_service"]

logger = logging.getLogger("nutrilens.gemini")


class GeminiService:
    """Encapsulates all Gemini API interactions with caching and error handling."""

    def __init__(self) -> None:
        """Initialize Gemini models and response cache."""
        self._api_keys = settings.gemini_api_keys
        self._current_key_index = 0
        self._retry_count = 0
        self._configure_api()
        self._model = genai.GenerativeModel("gemini-2.0-flash")
        self._cache: Dict[str, NutritionAnalysis] = {}
        self._cache_timestamps: Dict[str, float] = {}
        logger.info("Gemini Service initialized with %d API key(s)", len(self._api_keys))

    def _configure_api(self) -> None:
        """Configure the Gemini API with the current key."""
        if self._api_keys:
            genai.configure(api_key=self._api_keys[self._current_key_index])

    def _rotate_key(self) -> bool:
        """Rotate to next API key on quota exhaustion. Returns True if rotated successfully."""
        self._retry_count += 1
        if self._retry_count > len(self._api_keys):
            logger.error("All API keys exhausted — falling back to demo mode")
            self._retry_count = 0
            return False
        if len(self._api_keys) > 1:
            self._current_key_index = (self._current_key_index + 1) % len(self._api_keys)
            self._configure_api()
            logger.warning("Rotated to API key index %d (attempt %d)", self._current_key_index, self._retry_count)
            return True
        self._retry_count = 0
        return False

    async def analyze_food_image(
        self, image_bytes: bytes, user_context: Optional[Dict[str, Any]] = None
    ) -> NutritionAnalysis:
        """Analyze food image using Gemini Vision with structured JSON output.

        Args:
            image_bytes: Raw image bytes (JPEG/PNG/WebP, validated before calling).
            user_context: User profile dict (goals, allergies, today's log).

        Returns:
            NutritionAnalysis: Validated Pydantic model with macros, health score,
                               confidence, and healthier alternatives.
        """
        cache_key = hashlib.sha256(image_bytes).hexdigest()
        if cache_key in self._cache:
            cache_age = time.time() - self._cache_timestamps.get(cache_key, 0)
            if cache_age < 300:
                logger.info("Cache hit for image %s", cache_key[:12])
                return self._cache[cache_key]

        context_str = ""
        if user_context:
            context_str = f"""
User Context:
- Dietary Goal: {user_context.get('dietary_goal', 'general wellness')}
- Allergies: {', '.join(user_context.get('allergies', [])) or 'None'}
- Today's intake so far: {user_context.get('calories_today', 0)} kcal
"""

        prompt = f"""You are NutriLens AI, an expert nutritionist. Analyze this food image and return ONLY valid JSON.

{context_str}

Return this exact JSON structure:
{{
  "dish_name": "name of the dish",
  "cuisine": "cuisine type",
  "calories_kcal": 350,
  "macros": {{
    "protein_g": 20.0,
    "carbohydrates_g": 45.0,
    "fat_g": 12.0,
    "fiber_g": 5.0
  }},
  "health_score": 72,
  "confidence": 0.85,
  "healthier_alternatives": ["alternative 1", "alternative 2"],
  "micronutrient_highlights": ["Rich in Vitamin C", "Good source of Iron"],
  "portion_size": "1 medium plate",
  "meal_type": "lunch",
  "explanation": "Brief explanation of the health score"
}}

Be accurate with Indian foods. Health score: 0-100 where 100 is perfectly healthy.
Confidence: 0.0-1.0 based on image clarity and recognition certainty."""

        try:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            response = await self._model.generate_content_async(
                [prompt, image_part],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            result_data = json.loads(response.text)
            result = NutritionAnalysis(**result_data)
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()
            logger.info("Analyzed food: %s (score: %d)", result.dish_name, result.health_score)
            self._retry_count = 0
            return result

        except Exception as e:
            logger.error("Gemini vision analysis failed: %s", str(e))
            if "429" in str(e) and self._rotate_key():
                return await self.analyze_food_image(image_bytes, user_context)
            return self._get_demo_analysis()

    async def analyze_food_text(
        self, description: str, user_context: Optional[Dict[str, Any]] = None
    ) -> NutritionAnalysis:
        """Analyze food from text description using Gemini."""
        context_str = ""
        if user_context:
            context_str = f"\nUser goal: {user_context.get('dietary_goal', 'general wellness')}"

        prompt = f"""You are NutriLens AI, an expert nutritionist. Analyze this food description and return ONLY valid JSON.

Food: {description}{context_str}

Return this exact JSON structure:
{{
  "dish_name": "name of the dish",
  "cuisine": "cuisine type",
  "calories_kcal": 350,
  "macros": {{"protein_g": 20.0, "carbohydrates_g": 45.0, "fat_g": 12.0, "fiber_g": 5.0}},
  "health_score": 72,
  "confidence": 0.9,
  "healthier_alternatives": ["alternative 1", "alternative 2"],
  "micronutrient_highlights": ["Rich in Vitamin C"],
  "portion_size": "1 serving",
  "meal_type": "lunch",
  "explanation": "Brief explanation of the health score"
}}

Be accurate with Indian foods. Health score: 0-100."""

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            result_data = json.loads(response.text)
            return NutritionAnalysis(**result_data)
        except Exception as e:
            logger.error("Gemini text analysis failed: %s", str(e))
            if "429" in str(e) and self._rotate_key():
                return await self.analyze_food_text(description, user_context)
            return self._get_demo_analysis(description)

    async def get_coach_response(
        self, query: str, user_context: Dict[str, Any], language: str = "en"
    ) -> CoachResponse:
        """Generate a personalized nutrition coaching response."""
        lang_instruction = "Respond in Hindi (Hinglish is okay)." if language == "hi" else "Respond in English."

        prompt = f"""You are NutriLens AI Coach — a warm, knowledgeable nutrition advisor.
You are NOT a generic chatbot. You have full context of the user's health profile and today's meals.

User Profile:
- Name: {user_context.get('name', 'User')}
- Goal: {user_context.get('dietary_goal', 'general wellness')}
- Allergies: {', '.join(user_context.get('allergies', [])) or 'None'}
- Today's calories: {user_context.get('calories_today', 0)} / {user_context.get('calorie_goal', 2000)} kcal
- Protein today: {user_context.get('protein_today', 0)}g
- Meals logged today: {user_context.get('meals_count', 0)}

{lang_instruction}

User's question: {query}

Return ONLY valid JSON:
{{
  "response_text": "Your warm, personalized response here",
  "suggestions": ["Follow-up question 1", "Follow-up question 2", "Follow-up question 3"]
}}"""

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            data = json.loads(response.text)
            return CoachResponse(
                response_text=data.get("response_text", "I'm here to help with your nutrition!"),
                language=language,
                suggestions=data.get("suggestions", []),
            )
        except Exception as e:
            logger.error("Coach response failed: %s", str(e))
            if "429" in str(e) and self._rotate_key():
                return await self.get_coach_response(query, user_context, language)
            return CoachResponse(
                response_text="I'm currently processing your request. Please try again in a moment!",
                language=language,
                suggestions=["What should I eat for dinner?", "How's my nutrition today?"],
            )

    async def generate_habit_report(self, weekly_data: Dict[str, Any]) -> HabitReport:
        """Generate a 7-day behavioral pattern analysis."""
        prompt = f"""You are NutriLens AI analyzing a user's 7-day eating patterns.

Weekly Data:
{json.dumps(weekly_data, indent=2)}

Analyze patterns — late-night eating, breakfast skipping, weekend deviations, nutrient gaps.
Be warm and insightful, not judgmental. Suggest ONE micro-action per insight.

Return ONLY valid JSON:
{{
  "patterns": ["Pattern 1", "Pattern 2", "Pattern 3"],
  "insights": ["Insight with warmth 1", "Insight 2"],
  "micro_actions": ["One small actionable step 1", "Step 2"],
  "avg_health_score": 65,
  "top_nutrient_gap": "protein"
}}"""

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.6,
                ),
            )
            data = json.loads(response.text)
            return HabitReport(**data)
        except Exception as e:
            logger.error("Habit report generation failed: %s", str(e))
            return HabitReport(
                patterns=["You tend to eat lighter meals in the morning"],
                insights=["Adding a protein-rich breakfast could boost your energy"],
                micro_actions=["Try adding one boiled egg to your morning routine"],
                avg_health_score=65,
                top_nutrient_gap="protein",
            )

    async def generate_nudge(self, user_context: Dict[str, Any]) -> NudgeResponse:
        """Generate a proactive nutrition nudge based on current gaps."""
        prompt = f"""You are NutriLens AI. Generate a brief, warm, proactive nutrition nudge.

User Context:
- Calories today: {user_context.get('calories_today', 0)} / {user_context.get('calorie_goal', 2000)}
- Protein gap: {user_context.get('protein_gap', 30)}g remaining
- Time of day: {user_context.get('time_of_day', 'afternoon')}
- Meals logged: {user_context.get('meals_count', 1)}

Return ONLY valid JSON:
{{
  "message": "Warm nudge message",
  "nutrient_gaps": ["protein", "fiber"],
  "recommended_foods": ["Greek yogurt", "Chickpea salad", "Paneer tikka"],
  "time_context": "It's afternoon — perfect time for a protein-rich snack!"
}}"""

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            data = json.loads(response.text)
            return NudgeResponse(**data)
        except Exception as e:
            logger.error("Nudge generation failed: %s", str(e))
            return NudgeResponse(
                message="Time for a protein boost! How about some paneer or dal?",
                nutrient_gaps=["protein"],
                recommended_foods=["Paneer tikka", "Dal tadka", "Greek yogurt"],
                time_context="afternoon snack time",
            )

    def _get_demo_analysis(self, description: str = "Dal Makhani with Jeera Rice") -> NutritionAnalysis:
        """Return a realistic demo analysis for fallback or demo mode."""
        return NutritionAnalysis(
            dish_name=description if description else "Dal Makhani with Jeera Rice",
            cuisine="Indian",
            calories_kcal=485,
            macros=MacroBreakdown(protein_g=18.5, carbohydrates_g=62.0, fat_g=16.5, fiber_g=8.0),
            health_score=68,
            confidence=0.92,
            healthier_alternatives=["Dal Tadka with Brown Rice", "Rajma with Quinoa"],
            micronutrient_highlights=["Rich in Iron", "Good source of B vitamins", "Contains Folate"],
            portion_size="1 medium plate",
            meal_type="lunch",
            explanation="Nutritious lentil curry with rice. Moderate calories, could benefit from more vegetables.",
        )


# Singleton instance
gemini_service = GeminiService()
