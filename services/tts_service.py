"""
NutriLens TTS Service
========================
Purpose: Google Cloud Text-to-Speech API for voice coach audio responses.
Inputs:  Text string, language code (en-IN / hi-IN)
Outputs: Base64-encoded MP3 audio bytes
Deps:    httpx>=0.27.0
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

import httpx

from config import settings

__all__ = ["TTSService", "tts_service"]

logger = logging.getLogger("nutrilens.tts")


class TTSService:
    """Google Cloud Text-to-Speech for coach voice responses."""

    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key  # Uses same API key
        self._base_url = "https://texttospeech.googleapis.com/v1/text:synthesize"

    async def synthesize_speech(
        self, text: str, language: str = "en"
    ) -> Optional[str]:
        """Convert text to speech audio (base64 MP3)."""
        lang_code = "hi-IN" if language == "hi" else "en-IN"
        voice_name = f"{lang_code}-Wavenet-D"

        if not self._api_key:
            logger.info("No API key for TTS — returning None")
            return None

        try:
            body = {
                "input": {"text": text[:5000]},
                "voice": {
                    "languageCode": lang_code,
                    "name": voice_name,
                    "ssmlGender": "FEMALE",
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 1.0,
                    "pitch": 0.0,
                },
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}?key={self._api_key}",
                    json=body,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("audioContent")

        except Exception as e:
            logger.error("TTS synthesis failed: %s", str(e))
            return None


tts_service = TTSService()
