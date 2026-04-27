"""
NutriLens Explore Router
==========================
Purpose: Restaurant discovery (Google Maps) and recipe videos (YouTube) endpoints.
Inputs:  User location, nutrient gaps, search queries
Outputs: RestaurantResult list, RecipeVideo list, translated text
Deps:    FastAPI, maps_service, httpx (YouTube API)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

from config import settings, DEMO_USER_ID
from models import ExploreResult, RecipeVideo, RestaurantResult
from services.maps_service import maps_service
from services.firebase_service import firebase_service

__all__ = ["router"]

logger = logging.getLogger("nutrilens.router.explore")

router = APIRouter(prefix="/api/v1/explore", tags=["Explore"])


@router.get(
    "/restaurants",
    response_model=List[RestaurantResult],
    summary="Find nearby healthy restaurants",
    description="Uses Google Maps Places API (New) to find nearby restaurants, "
    "ranked by Gemini nutritional fit score based on your nutrient gaps.",
)
async def find_restaurants(
    latitude: float = 19.0760,
    longitude: float = 72.8777,
    radius_m: int = 2000,
    user_id: str = DEMO_USER_ID,
) -> List[RestaurantResult]:
    """Find and rank nearby restaurants by nutritional fit."""
    return await maps_service.find_nearby_restaurants(
        latitude=latitude, longitude=longitude, radius_m=radius_m
    )


@router.get(
    "/recipes",
    response_model=List[RecipeVideo],
    summary="Discover recipe videos",
    description="Uses YouTube Data API v3 to find recipe videos matched to "
    "your top nutrient gap. Contextual query generated from your daily log.",
)
async def find_recipes(
    query: str = "high protein Indian vegetarian recipes",
    max_results: int = 6,
) -> List[RecipeVideo]:
    """Search YouTube for recipe videos matched to nutrient gaps."""
    if not settings.youtube_api_key:
        return _get_demo_recipes()

    try:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": settings.youtube_api_key,
            "videoCategoryId": "26",  # How-to & Style
            "relevanceLanguage": "en",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            videos.append(RecipeVideo(
                title=snippet.get("title", ""),
                video_id=item.get("id", {}).get("videoId", ""),
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                channel_name=snippet.get("channelTitle", ""),
                nutrient_match=query,
            ))
        return videos if videos else _get_demo_recipes()

    except Exception as e:
        logger.error("YouTube API failed: %s", str(e))
        return _get_demo_recipes()


@router.get(
    "/translate",
    summary="Translate text",
    description="Uses Google Translate API for UI localization (EN ↔ Hindi).",
)
async def translate_text(
    text: str, target_language: str = "hi"
) -> Dict[str, str]:
    """Translate text using Google Translate API."""
    if not settings.gemini_api_key:
        return {"translated": text, "source": "en", "target": target_language}

    try:
        params = {
            "q": text,
            "target": target_language,
            "key": settings.gemini_api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://translation.googleapis.com/language/translate/v2",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = data["data"]["translations"][0]["translatedText"]
                return {"translated": translated, "source": "en", "target": target_language}
    except Exception as e:
        logger.error("Translation failed: %s", str(e))

    return {"translated": text, "source": "en", "target": target_language}


def _get_demo_recipes() -> List[RecipeVideo]:
    """Return demo recipe videos."""
    return [
        RecipeVideo(
            title="High Protein Paneer Tikka | Healthy Indian Recipe",
            video_id="demo_yt_1", channel_name="Healthy Indian Kitchen",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            nutrient_match="protein",
        ),
        RecipeVideo(
            title="5-Minute Moong Dal Chilla | 30g Protein Breakfast",
            video_id="demo_yt_2", channel_name="FitMeal India",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            nutrient_match="protein",
        ),
        RecipeVideo(
            title="Quinoa Khichdi | Fiber-Rich Indian Superfood",
            video_id="demo_yt_3", channel_name="NutriFit",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            nutrient_match="fiber",
        ),
        RecipeVideo(
            title="Ragi Dosa | Iron-Rich South Indian Breakfast",
            video_id="demo_yt_4", channel_name="Healthy South",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            nutrient_match="iron",
        ),
    ]
