"""
NutriLens Nutrition Analysis Tests
====================================
Tests for food image/text analysis endpoints and Gemini service.
All external services (Gemini, Firebase) are mocked.
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from tests.conftest import MOCK_NUTRITION


class TestNutritionAnalyzeImage:
    """Tests for POST /api/v1/nutrition/analyze."""

    def test_analyze_rejects_invalid_mime_type(self, client):
        """Verify that non-image files are rejected with 400."""
        resp = client.post(
            "/api/v1/nutrition/analyze",
            files={"image": ("test.txt", b"not an image", "text/plain")},
            data={"user_id": "test"},
        )
        assert resp.status_code == 400
        assert "Invalid image type" in resp.json()["detail"]

    def test_analyze_rejects_oversized_image(self, client):
        """Verify that images over 10MB are rejected with 413."""
        large_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * (11 * 1024 * 1024)
        resp = client.post(
            "/api/v1/nutrition/analyze",
            files={"image": ("big.jpg", large_bytes, "image/jpeg")},
        )
        assert resp.status_code == 413

    def test_analyze_rejects_tiny_image(self, client):
        """Verify that corrupted/tiny images are rejected."""
        resp = client.post(
            "/api/v1/nutrition/analyze",
            files={"image": ("tiny.jpg", b'\xff\xd8', "image/jpeg")},
        )
        assert resp.status_code == 400

    @patch("routers.nutrition.gemini_service.analyze_food_image", new_callable=AsyncMock)
    @patch("routers.nutrition.firebase_service.get_user_profile", new_callable=AsyncMock)
    @patch("routers.nutrition.firebase_service.get_daily_log", new_callable=AsyncMock)
    @patch("routers.nutrition.firebase_service.log_meal", new_callable=AsyncMock)
    @patch("routers.nutrition.sheets_service.export_meal", new_callable=AsyncMock)
    def test_analyze_returns_structured_output(
        self, mock_sheets, mock_log, mock_daily, mock_profile, mock_gemini, client
    ):
        """Ensures Gemini Vision returns a validated NutritionAnalysis."""
        mock_gemini.return_value = MOCK_NUTRITION
        mock_profile.return_value = {"dietary_goal": "general_wellness", "allergies": []}
        mock_daily.return_value = {"total_calories": 500}
        mock_log.return_value = {}

        image_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 2000
        resp = client.post(
            "/api/v1/nutrition/analyze",
            files={"image": ("food.jpg", image_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dish_name"] == "Paneer Tikka"
        assert 0 <= data["health_score"] <= 100
        assert data["calories_kcal"] > 0
        assert "protein_g" in data["macros"]
        assert len(data["healthier_alternatives"]) >= 1


class TestNutritionAnalyzeText:
    """Tests for POST /api/v1/nutrition/analyze-text."""

    @patch("routers.nutrition.gemini_service.analyze_food_text", new_callable=AsyncMock)
    def test_text_analysis_returns_result(self, mock_gemini, client):
        """Test text-based food analysis returns structured output."""
        mock_gemini.return_value = MOCK_NUTRITION
        resp = client.post(
            "/api/v1/nutrition/analyze-text",
            json={"description": "2 chapati with dal tadka"},
        )
        assert resp.status_code == 200
        assert resp.json()["dish_name"] == "Paneer Tikka"

    def test_text_analysis_rejects_empty(self, client):
        """Test that empty description is rejected."""
        resp = client.post(
            "/api/v1/nutrition/analyze-text",
            json={"description": "ab"},
        )
        assert resp.status_code == 422


class TestNutritionHistory:
    """Tests for GET /api/v1/nutrition/history."""

    def test_history_returns_daily_log(self, client):
        """Test meal history endpoint returns data."""
        resp = client.get("/api/v1/nutrition/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "meals" in data or "date" in data
