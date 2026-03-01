"""API tests: health, profile status, and profile validation."""

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "db" in data


def test_profile_status_when_empty(client: TestClient):
    response = client.get("/profile/status")
    assert response.status_code == 200
    data = response.json()
    assert data.get("exists") is False
    assert data.get("default_profile_id") is None
    assert data.get("profiles") == []


def test_profile_default_returns_404_for_invalid_id(client: TestClient):
    response = client.post("/profile/default", data={"profile_id": "nonexistent-uuid"})
    assert response.status_code == 404
    assert "not found" in response.json().get("detail", "").lower()


def test_progress_returns_empty_when_no_profiles(client: TestClient):
    response = client.get("/progress")
    assert response.status_code == 200
    data = response.json()
    assert data.get("weak") == []
    assert data.get("strong") == []
    assert data.get("suggested_next") == ""


def test_progress_returns_404_for_invalid_profile_id(client: TestClient):
    response = client.get("/progress", params={"profile_id": "nonexistent-uuid"})
    assert response.status_code == 404


def test_chat_returns_503_when_no_profile(client: TestClient):
    response = client.post(
        "/chat",
        json={"message": "Hello", "session_id": "test", "profile_id": ""},
    )
    assert response.status_code == 503


def test_chat_returns_404_for_invalid_profile_id(client: TestClient):
    """When a profile exists but profile_id is invalid, chat returns 404."""
    from db import save_profile, set_default_profile_id

    save_profile("real-profile-id", "Test", {})
    set_default_profile_id("real-profile-id")
    response = client.post(
        "/chat",
        json={
            "message": "Hello",
            "session_id": "test",
            "profile_id": "nonexistent-uuid",
        },
    )
    assert response.status_code == 404
