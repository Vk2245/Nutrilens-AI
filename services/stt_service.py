"""
NutriLens STT Service
========================
Purpose: Google Cloud Speech-to-Text for voice input in nutrition coach.
Inputs:  Base64-encoded audio bytes, language preference (en-IN / hi-IN)
Outputs: Transcribed text string
Deps:    httpx>=0.27.0
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import settings

__all__ = ["STTService", "stt_service"]

logger = logging.getLogger("nutrilens.stt")


class STTService:
    """Google Cloud Speech-to-Text for bilingual voice input."""

    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key
        self._base_url = "https://speech.googleapis.com/v1/speech:recognize"

    async def transcribe_audio(
        self, audio_base64: str, language: str = "en"
    ) -> Optional[str]:
        """Transcribe audio to text using Google Cloud STT.

        Args:
            audio_base64: Base64-encoded audio (WAV/WebM/OGG).
            language: Language code (en or hi) for primary recognition.

        Returns:
            Transcribed text or None on failure.
        """
        lang_code = "hi-IN" if language == "hi" else "en-IN"

        if not self._api_key:
            return "Demo: What should I eat for dinner tonight?"

        try:
            body = {
                "config": {
                    "encoding": "WEBM_OPUS",
                    "sampleRateHertz": 48000,
                    "languageCode": lang_code,
                    "alternativeLanguageCodes": ["en-IN", "hi-IN"],
                    "enableAutomaticPunctuation": True,
                    "model": "latest_long",
                },
                "audio": {"content": audio_base64},
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}?key={self._api_key}",
                    json=body,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            if results:
                return results[0]["alternatives"][0]["transcript"]
            return None

        except Exception as e:
            logger.error("STT transcription failed: %s", str(e))
            return None


stt_service = STTService()
