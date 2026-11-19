from conftest import make_user


def place_order(client, admin_headers, user_headers):
    """Admin creates a product, the customer orders it. Returns the order id."""
    product = client.post(
        "/products",
        json={"name": "Test Item", "price": 100.0, "stock": 10},
        headers=admin_headers,
    )
    product_id = product.json()["id"]
    order = client.post(
        "/orders",
        json={"items": [{"product_id": product_id, "quantity": 1}]},
        headers=user_headers,
    )
    return order.json()["id"]


def test_payment_happy_path(client, admin_headers, user_headers):
    order_id = place_order(client, admin_headers, user_headers)

    created = client.post("/payments", json={"order_id": order_id}, headers=user_headers)
    assert created.status_code == 201
    payment = created.json()
    assert payment["status"] == "created"

    checkout = client.post(
        f"/payments/{payment['id']}/simulate-checkout", headers=user_headers
    )
    assert checkout.status_code == 200

    verified = client.post("/payments/verify", json=checkout.json(), headers=user_headers)
    assert verified.status_code == 200
    assert verified.json()["status"] == "paid"

    order = client.get(f"/orders/{order_id}", headers=user_headers)
    assert order.json()["status"] == "paid"

    # Verifying again is safe
    again = client.post("/payments/verify", json=checkout.json(), headers=user_headers)
    assert again.status_code == 200
    assert again.json()["status"] == "paid"


def test_bad_signature_rejected(client, admin_headers, user_headers):
    order_id = place_order(client, admin_headers, user_headers)
    payment = client.post(
        "/payments", json={"order_id": order_id}, headers=user_headers
    ).json()
    checkout = client.post(
        f"/payments/{payment['id']}/simulate-checkout", headers=user_headers
    ).json()

    checkout["signature"] = "0" * 64
    response = client.post("/payments/verify", json=checkout, headers=user_headers)
    assert response.status_code == 400

    order = client.get(f"/orders/{order_id}", headers=user_headers)
    assert order.json()["status"] == "placed"


def test_cannot_pay_another_users_order(client, admin_headers, user_headers):
    order_id = place_order(client, admin_headers, user_headers)
    other_headers = make_user(client, "other@example.com")

    response = client.post(
        "/payments", json={"order_id": order_id}, headers=other_headers
    )
    assert response.status_code == 404


def test_create_payment_twice_returns_same_payment(client, admin_headers, user_headers):
    order_id = place_order(client, admin_headers, user_headers)

    first = client.post("/payments", json={"order_id": order_id}, headers=user_headers)
    second = client.post("/payments", json={"order_id": order_id}, headers=user_headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["provider_order_id"] == second.json()["provider_order_id"]


def test_payments_require_login(client):
    response = client.post("/payments", json={"order_id": 1})
    assert response.status_code in (401, 403)
    