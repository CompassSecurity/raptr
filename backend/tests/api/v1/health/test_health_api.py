from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test health check endpoint returns successful response
    """
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "database" in data["message"].lower() or "online" in data["message"].lower()


def test_health_check_returns_dict(client: TestClient):
    """
    Test health check returns a properly formatted dictionary
    """
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
