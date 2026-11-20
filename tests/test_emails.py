def test_order_sends_confirmation_email(
    client, admin_headers, user_headers, monkeypatch
):
    sent = []
    monkeypatch.setattr(
        "app.routers.orders.send_order_confirmation",
        lambda to_email, order_id, total: sent.append((to_email, order_id, total)),
    )

    product = client.post(
        "/products",
        json={"name": "Test Item", "price": 100.0, "stock": 10},
        headers=admin_headers,
    ).json()
    response = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
        headers=user_headers,
    )

    assert response.status_code == 201
    assert sent == [("user@example.com", response.json()["id"], 200.0)]