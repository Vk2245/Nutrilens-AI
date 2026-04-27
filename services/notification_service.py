"""
NutriLens Notification Service
================================
Purpose: FCM push notification dispatch with Gemini-generated content.
Inputs:  User FCM tokens, notification type, context data
Outputs: Push notification delivery status
Deps:    firebase-admin>=6.5.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from config import settings

__all__ = ["NotificationService", "notification_service"]

logger = logging.getLogger("nutrilens.notifications")


class NotificationService:
    """Firebase Cloud Messaging for proactive meal nudges."""

    async def send_meal_nudge(
        self, fcm_token: str, nudge_text: str, title: str = "NutriLens Nudge 🥗"
    ) -> bool:
        """Send a proactive meal nudge notification via FCM."""
        try:
            from services.firebase_service import firebase_service
            return await firebase_service.send_push_notification(
                token=fcm_token,
                title=title,
                body=nudge_text,
            )
        except Exception as e:
            logger.error("Nudge notification failed: %s", str(e))
            return False

    async def send_streak_celebration(
        self, fcm_token: str, streak_count: int
    ) -> bool:
        """Send a streak milestone celebration notification."""
        title = f"🔥 {streak_count}-Day Streak!"
        body = f"Amazing! You've logged meals for {streak_count} days straight. Keep the momentum going!"
        try:
            from services.firebase_service import firebase_service
            return await firebase_service.send_push_notification(
                token=fcm_token, title=title, body=body,
            )
        except Exception as e:
            logger.error("Streak notification failed: %s", str(e))
            return False


notification_service = NotificationService()
