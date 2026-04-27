"""
NutriLens Coach Router
========================
Purpose: Voice and text-based nutrition coaching endpoints.
Inputs:  Text queries, audio (base64), language preference
Outputs: CoachResponse with text, optional audio, and suggestions
Deps:    FastAPI, gemini_service, tts_service, stt_service
"""

from __future__ import annotations

import logging
from fastapi import APIRouter
from models import CoachQueryRequest, CoachResponse, HabitReport, NudgeResponse
from services.gemini_service import gemini_service
from services.firebase_service import firebase_service
from services.tts_service import tts_service
from services.stt_service import stt_service
from config import DEMO_USER_ID

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.coach")

router = APIRouter(prefix="/api/v1/coach", tags=["Nutrition Coach"])


@router.post(
    "/ask",
    response_model=CoachResponse,
    summary="Ask the AI nutrition coach",
    description="Send a text query to the Gemini-powered nutrition coach. "
    "Returns personalized advice based on your profile and today's meals.",
)
async def ask_coach(
    request: CoachQueryRequest, user_id: str = DEMO_USER_ID
) -> CoachResponse:
    """Text-based nutrition coaching with full user context."""
    profile = await firebase_service.get_user_profile(user_id)
    daily_log = await firebase_service.get_daily_log(user_id)

    user_context = {
        "name": profile.get("name", "User"),
        "dietary_goal": profile.get("dietary_goal", "general_wellness"),
        "allergies": profile.get("allergies", []),
        "calories_today": daily_log.get("total_calories", 0),
        "calorie_goal": daily_log.get("calorie_goal", 2000),
        "protein_today": daily_log.get("total_protein_g", 0),
        "meals_count": len(daily_log.get("meals", [])),
    }

    response = await gemini_service.get_coach_response(
        request.query, user_context, request.language
    )

    # Optional TTS audio
    if request.include_audio:
        audio = await tts_service.synthesize_speech(
            response.response_text, request.language
        )
        response.audio_base64 = audio

    return response


@router.post(
    "/voice",
    response_model=CoachResponse,
    summary="Voice nutrition coaching",
    description="Send audio input for bilingual voice coaching (en-IN + hi-IN). "
    "Returns text + audio response.",
)
async def voice_coach(
    audio_base64: str, language: str = "en", user_id: str = DEMO_USER_ID
) -> CoachResponse:
    """Full voice loop: STT → Gemini → TTS."""
    # Transcribe audio to text
    transcript = await stt_service.transcribe_audio(audio_base64, language)
    if not transcript:
        return CoachResponse(
            response_text="I couldn't understand the audio. Could you try again?",
            language=language,
            suggestions=["What should I eat for dinner?", "Am I eating enough protein?"],
        )

    # Get coach response
    profile = await firebase_service.get_user_profile(user_id)
    daily_log = await firebase_service.get_daily_log(user_id)
    user_context = {
        "name": profile.get("name", "User"),
        "dietary_goal": profile.get("dietary_goal", "general_wellness"),
        "allergies": profile.get("allergies", []),
        "calories_today": daily_log.get("total_calories", 0),
        "calorie_goal": daily_log.get("calorie_goal", 2000),
        "protein_today": daily_log.get("total_protein_g", 0),
        "meals_count": len(daily_log.get("meals", [])),
    }

    response = await gemini_service.get_coach_response(transcript, user_context, language)

    # Generate audio response
    audio = await tts_service.synthesize_speech(response.response_text, language)
    response.audio_base64 = audio

    return response


@router.get(
    "/nudge",
    response_model=NudgeResponse,
    summary="Get proactive nutrition nudge",
    description="Gemini generates a context-aware nutrition nudge based on "
    "current nutritional gaps, time of day, and user profile.",
)
async def get_nudge(user_id: str = DEMO_USER_ID) -> NudgeResponse:
    """Generate a proactive nutrition nudge."""
    profile = await firebase_service.get_user_profile(user_id)
    daily_log = await firebase_service.get_daily_log(user_id)

    import datetime
    hour = datetime.datetime.now().hour
    time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"

    calorie_goal = daily_log.get("calorie_goal", 2000)
    calories_today = daily_log.get("total_calories", 0)
    protein_today = daily_log.get("total_protein_g", 0)

    user_context = {
        "calories_today": calories_today,
        "calorie_goal": calorie_goal,
        "protein_gap": max(0, 50 - protein_today),
        "time_of_day": time_of_day,
        "meals_count": len(daily_log.get("meals", [])),
    }

    return await gemini_service.generate_nudge(user_context)


@router.get(
    "/habit-report",
    response_model=HabitReport,
    summary="Get 7-day habit report",
    description="Gemini analyzes your eating patterns over 7 days and generates "
    "behavioral insights with actionable micro-steps.",
)
async def get_habit_report(user_id: str = DEMO_USER_ID) -> HabitReport:
    """Generate a 7-day behavioral pattern analysis."""
    weekly_logs = await firebase_service.get_weekly_logs(user_id)
    weekly_data = {
        "user_id": user_id,
        "days": [
            {
                "date": log.get("date", ""),
                "total_calories": log.get("total_calories", 0),
                "meals_count": len(log.get("meals", [])),
                "avg_health_score": log.get("avg_health_score", 0),
            }
            for log in weekly_logs
        ],
    }
    return await gemini_service.generate_habit_report(weekly_data)
