"""
NutriLens Test Configuration
==============================
Purpose: Shared fixtures and mocks for the NutriLens test suite.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from models import MacroBreakdown, NutritionAnalysis, CoachResponse


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Minimal valid JPEG bytes for testing."""
    return b'\xff\xd8\xff\xe0' + b'\x00' * 2000


MOCK_NUTRITION = NutritionAnalysis(
    dish_name="Paneer Tikka",
    cuisine="Indian",
    calories_kcal=280,
    macros=MacroBreakdown(protein_g=22.0, carbohydrates_g=12.0, fat_g=18.0, fiber_g=3.0),
    health_score=75,
    confidence=0.92,
    healthier_alternatives=["Grilled Tofu Tikka", "Mushroom Tikka"],
    micronutrient_highlights=["Rich in Calcium", "Good source of Protein"],
    portion_size="6 pieces",
    meal_type="snack",
    explanation="High-protein appetizer. Moderate fat from paneer.",
)

MOCK_COACH_RESPONSE = CoachResponse(
    response_text="Great question! Based on your intake today, I'd suggest adding some dal or chickpeas for protein.",
    language="en",
    suggestions=["What about a protein shake?", "Show me fiber-rich foods"],
)
