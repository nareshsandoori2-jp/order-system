def test_signup_and_login(client):
    data = {"name": "Naresh", "email": "n@example.com", "password": "password123"}

    response = client.post("/auth/signup", json=data)
    assert response.status_code == 201
    assert response.json()["role"] == "customer"
    assert "password" not in response.json()

    response = client.post(
        "/auth/login", json={"email": "n@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_duplicate_email_rejected(client):
    data = {"name": "Naresh", "email": "n@example.com", "password": "password123"}
    client.post("/auth/signup", json=data)
    response = client.post("/auth/signup", json=data)
    assert response.status_code == 400


def test_wrong_password_rejected(client):
    data = {"name": "Naresh", "email": "n@example.com", "password": "password123"}
    client.post("/auth/signup", json=data)
    response = client.post(
        "/auth/login", json={"email": "n@example.com", "password": "wrongpass123"}
    )
    assert response.status_code == 401