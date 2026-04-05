def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "School OS API running"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_plans_endpoint_is_public(client):
    response = client.get("/api/billing/plans")

    assert response.status_code == 200
    data = response.json()
    assert "plans" in data
    assert len(data["plans"]) == 3


def test_protected_route_requires_auth(client):
    response = client.get("/api/students")

    assert response.status_code == 403


def test_login_with_wrong_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "wrong@email.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
