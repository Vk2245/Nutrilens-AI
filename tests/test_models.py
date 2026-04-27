"""
NutriLens Pydantic Model Tests
=================================
Tests for all Pydantic v2 model validations, field constraints, and sanitization.
"""

import pytest
from pydantic import ValidationError
from models import (
    MacroBreakdown, NutritionAnalysis, MealEntry, UserProfile,
    CoachQueryRequest, FoodAnalyzeRequest, OnboardingRequest,
    DietaryGoal, ActivityLevel,
)


class TestMacroBreakdown:
    """Tests for MacroBreakdown model validation."""

    def test_valid_macros(self):
        m = MacroBreakdown(protein_g=20, carbohydrates_g=45, fat_g=12, fiber_g=5)
        assert m.protein_g == 20

    def test_negative_values_rejected(self):
        with pytest.raises(ValidationError):
            MacroBreakdown(protein_g=-1, carbohydrates_g=45, fat_g=12, fiber_g=5)


class TestNutritionAnalysis:
    """Tests for NutritionAnalysis model validation."""

    def test_valid_analysis(self):
        a = NutritionAnalysis(
            dish_name="Dal Tadka", calories_kcal=320,
            macros=MacroBreakdown(protein_g=15, carbohydrates_g=40, fat_g=12, fiber_g=8),
            health_score=78, confidence=0.9,
        )
        assert a.health_score == 78

    def test_health_score_bounds(self):
        with pytest.raises(ValidationError):
            NutritionAnalysis(
                dish_name="Test", calories_kcal=100,
                macros=MacroBreakdown(protein_g=5, carbohydrates_g=10, fat_g=3, fiber_g=2),
                health_score=150, confidence=0.5,
            )

    def test_empty_dish_name_rejected(self):
        with pytest.raises(ValidationError):
            NutritionAnalysis(
                dish_name="", calories_kcal=100,
                macros=MacroBreakdown(protein_g=5, carbohydrates_g=10, fat_g=3, fiber_g=2),
                health_score=50, confidence=0.5,
            )

    def test_calories_upper_bound(self):
        with pytest.raises(ValidationError):
            NutritionAnalysis(
                dish_name="Test", calories_kcal=6000,
                macros=MacroBreakdown(protein_g=5, carbohydrates_g=10, fat_g=3, fiber_g=2),
                health_score=50, confidence=0.5,
            )


class TestCoachQueryRequest:
    """Tests for CoachQueryRequest validation."""

    def test_valid_query(self):
        q = CoachQueryRequest(query="What should I eat?", language="en")
        assert q.language == "en"

    def test_html_stripped(self):
        q = CoachQueryRequest(query="<script>alert('xss')</script>What?", language="en")
        assert "<script>" not in q.query

    def test_invalid_language_rejected(self):
        with pytest.raises(ValidationError):
            CoachQueryRequest(query="test", language="fr")


class TestFoodAnalyzeRequest:
    """Tests for FoodAnalyzeRequest validation."""

    def test_valid_request(self):
        r = FoodAnalyzeRequest(description="2 chapati with dal")
        assert len(r.description) > 0

    def test_short_description_rejected(self):
        with pytest.raises(ValidationError):
            FoodAnalyzeRequest(description="ab")

    def test_html_sanitized(self):
        r = FoodAnalyzeRequest(description="<b>Paneer</b> butter masala")
        assert "<b>" not in r.description


class TestOnboardingRequest:
    """Tests for OnboardingRequest validation."""

    def test_valid_onboarding(self):
        o = OnboardingRequest(
            name="Test User", age=25, weight_kg=65, height_cm=170,
            dietary_goal=DietaryGoal.WEIGHT_LOSS,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        assert o.dietary_goal == DietaryGoal.WEIGHT_LOSS

    def test_age_bounds(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(name="Test", age=5, weight_kg=65, height_cm=170)

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(name="Test", age=25, weight_kg=10, height_cm=170)


class TestMealEntry:
    """Tests for MealEntry model."""

    def test_valid_meal(self):
        m = MealEntry(
            dish_name="Roti", calories_kcal=120,
            macros=MacroBreakdown(protein_g=4, carbohydrates_g=25, fat_g=1, fiber_g=2),
        )
        assert m.dish_name == "Roti"

    def test_html_stripped_from_name(self):
        m = MealEntry(
            dish_name="<img src=x>Roti", calories_kcal=120,
            macros=MacroBreakdown(protein_g=4, carbohydrates_g=25, fat_g=1, fiber_g=2),
        )
        assert "<img" not in m.dish_name
