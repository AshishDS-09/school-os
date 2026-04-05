def test_register_new_school(client):
    response = client.post(
        "/api/auth/register",
        json={
            "school_name": "Test School",
            "school_email": "admin@testschool.com",
            "school_phone": "9999999999",
            "school_city": "Delhi",
            "school_state": "Delhi",
            "admin_first_name": "Test",
            "admin_last_name": "Admin",
            "admin_password": "testpass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["school_id"] is not None


def test_register_then_login(client):
    client.post(
        "/api/auth/register",
        json={
            "school_name": "Login Test School",
            "school_email": "login@test.com",
            "school_phone": "8888888888",
            "school_city": "Mumbai",
            "school_state": "Maharashtra",
            "admin_first_name": "Login",
            "admin_last_name": "Test",
            "admin_password": "mypassword123",
        },
    )

    response = client.post(
        "/api/auth/login",
        data={"username": "login@test.com", "password": "mypassword123"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_duplicate_school_email_rejected(client):
    payload = {
        "school_name": "Dup School",
        "school_email": "dup@school.com",
        "school_phone": "7777777777",
        "school_city": "Pune",
        "school_state": "Maharashtra",
        "admin_first_name": "Dup",
        "admin_last_name": "Admin",
        "admin_password": "duppass123",
    }

    client.post("/api/auth/register", json=payload)
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
