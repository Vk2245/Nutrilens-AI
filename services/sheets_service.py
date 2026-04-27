"""
NutriLens Sheets Service
==========================
Purpose: Google Sheets API integration for real-time meal log export.
Inputs:  Meal data, user ID, Google Sheet ID
Outputs: Appended rows in shared Google Sheet for data transparency
Deps:    gspread>=6.0.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from config import settings

__all__ = ["SheetsService", "sheets_service"]

logger = logging.getLogger("nutrilens.sheets")


class SheetsService:
    """Google Sheets API for meal log export using gspread."""

    def __init__(self) -> None:
        self._client = None
        self._sheet = None

    def initialize(self) -> None:
        """Initialize gspread client with service account credentials."""
        if not settings.google_sheets_id or not settings.google_credentials_path:
            logger.info("Sheets not configured — export disabled")
            return

        try:
            import gspread
            self._client = gspread.service_account(filename=settings.google_credentials_path)
            self._sheet = self._client.open_by_key(settings.google_sheets_id)
            logger.info("Google Sheets connected: %s", settings.google_sheets_id)
        except Exception as e:
            logger.warning("Sheets init failed: %s", str(e))

    async def export_meal(self, user_id: str, meal_data: Dict[str, Any]) -> bool:
        """Append a meal entry to the shared Google Sheet."""
        if not self._sheet:
            logger.debug("Sheets not initialized — skipping export")
            return False

        try:
            worksheet = self._sheet.sheet1
            row = [
                user_id,
                meal_data.get("dish_name", ""),
                meal_data.get("calories_kcal", 0),
                meal_data.get("macros", {}).get("protein_g", 0),
                meal_data.get("macros", {}).get("carbohydrates_g", 0),
                meal_data.get("macros", {}).get("fat_g", 0),
                meal_data.get("health_score", 0),
                meal_data.get("meal_type", ""),
                meal_data.get("timestamp", ""),
            ]
            worksheet.append_row(row)
            logger.info("Meal exported to Sheets: %s", meal_data.get("dish_name"))
            return True
        except Exception as e:
            logger.error("Sheets export failed: %s", str(e))
            return False


sheets_service = SheetsService()
