"""
NutriLens Coach Tests
=======================
Tests for text and voice coaching endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from tests.conftest import MOCK_COACH_RESPONSE


class TestCoachAsk:
    """Tests for POST /api/v1/coach/ask."""

    @patch("routers.coach.gemini_service.get_coach_response", new_callable=AsyncMock)
    @patch("routers.coach.firebase_service.get_user_profile", new_callable=AsyncMock)
    @patch("routers.coach.firebase_service.get_daily_log", new_callable=AsyncMock)
    def test_coach_returns_response(self, mock_daily, mock_profile, mock_gemini, client):
        """Test text coaching returns a valid CoachResponse."""
        mock_gemini.return_value = MOCK_COACH_RESPONSE
        mock_profile.return_value = {"name": "Test", "dietary_goal": "general_wellness", "allergies": []}
        mock_daily.return_value = {"total_calories": 500, "calorie_goal": 2000, "total_protein_g": 20, "meals": []}

        resp = client.post(
            "/api/v1/coach/ask",
            json={"query": "What should I eat for dinner?", "language": "en"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response_text" in data
        assert len(data["response_text"]) > 0

    def test_coach_rejects_empty_query(self, client):
        """Test empty query is rejected."""
        resp = client.post("/api/v1/coach/ask", json={"query": "", "language": "en"})
        assert resp.status_code == 422


class TestCoachNudge:
    """Tests for GET /api/v1/coach/nudge."""

    @patch("routers.coach.gemini_service.generate_nudge", new_callable=AsyncMock)
    @patch("routers.coach.firebase_service.get_user_profile", new_callable=AsyncMock)
    @patch("routers.coach.firebase_service.get_daily_log", new_callable=AsyncMock)
    def test_nudge_returns_response(self, mock_daily, mock_profile, mock_nudge, client):
        """Test nudge endpoint returns contextual recommendation."""
        from models import NudgeResponse
        mock_nudge.return_value = NudgeResponse(
            message="Try some paneer!", nutrient_gaps=["protein"],
            recommended_foods=["Paneer"], time_context="evening",
        )
        mock_profile.return_value = {"dietary_goal": "general_wellness"}
        mock_daily.return_value = {"total_calories": 1000, "calorie_goal": 2000, "total_protein_g": 20, "meals": []}

        resp = client.get("/api/v1/coach/nudge")
        assert resp.status_code == 200
        assert "message" in resp.json()


class TestCoachHabitReport:
    """Tests for GET /api/v1/coach/habit-report."""

    @patch("routers.coach.gemini_service.generate_habit_report", new_callable=AsyncMock)
    @patch("routers.coach.firebase_service.get_weekly_logs", new_callable=AsyncMock)
    def test_habit_report_returns_insights(self, mock_weekly, mock_habit, client):
        """Test 7-day habit report contains patterns and actions."""
        from models import HabitReport
        mock_habit.return_value = HabitReport(
            patterns=["Late dinner pattern"], insights=["Consider earlier meals"],
            micro_actions=["Set a dinner reminder at 7pm"], avg_health_score=65,
        )
        mock_weekly.return_value = [{"date": "2025-01-01", "total_calories": 1500, "meals": []}] * 7

        resp = client.get("/api/v1/coach/habit-report")
        assert resp.status_code == 200
        data = resp.json()
        assert "patterns" in data
        assert "micro_actions" in data
