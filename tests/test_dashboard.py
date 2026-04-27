"""NutriLens Dashboard Tests — daily/weekly summary and meal logging."""

from unittest.mock import AsyncMock, patch


class TestDashboardDaily:
    def test_daily_returns_data(self, client):
        resp = client.get("/api/v1/dashboard/daily")
        assert resp.status_code == 200
        data = resp.json()
        assert "daily_log" in data
        assert "profile" in data

class TestDashboardWeekly:
    def test_weekly_returns_data(self, client):
        resp = client.get("/api/v1/dashboard/weekly")
        assert resp.status_code == 200
        assert "weekly_logs" in resp.json()

class TestExplore:
    def test_restaurants_returns_list(self, client):
        resp = client.get("/api/v1/explore/restaurants")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_recipes_returns_list(self, client):
        resp = client.get("/api/v1/explore/recipes")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

class TestAuth:
    def test_demo_login(self, client):
        resp = client.get("/api/v1/auth/demo-login")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["name"] == "Priya Sharma"

    def test_get_profile(self, client):
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 200

class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_frontend_config(self, client):
        resp = client.get("/api/config/frontend")
        assert resp.status_code == 200
        assert "firebase" in resp.json()
