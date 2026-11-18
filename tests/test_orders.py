def create_product(client, admin_headers, stock=10):
    response = client.post(
        "/products",
        json={"name": "Laptop", "price": 1000, "stock": stock},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_customer_cannot_create_product(client, user_headers):
    response = client.post(
        "/products",
        json={"name": "Phone", "price": 500, "stock": 5},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_no_token_cannot_create_product(client):
    response = client.post(
        "/products", json={"name": "Phone", "price": 500, "stock": 5}
    )
    assert response.status_code in (401, 403)


def test_anyone_can_list_products(client, admin_headers):
    create_product(client, admin_headers)
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_order_reduces_stock_and_sets_total(client, admin_headers, user_headers):
    product = create_product(client, admin_headers, stock=10)

    response = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 3}]},
        headers=user_headers,
    )
    assert response.status_code == 201
    assert response.json()["total"] == 3000
    assert response.json()["status"] == "placed"

    stock = client.get(f"/products/{product['id']}").json()["stock"]
    assert stock == 7


def test_order_fails_when_stock_too_low(client, admin_headers, user_headers):
    product = create_product(client, admin_headers, stock=2)
    response = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 5}]},
        headers=user_headers,
    )
    assert response.status_code == 400


def test_cancel_restores_stock(client, admin_headers, user_headers):
    product = create_product(client, admin_headers, stock=10)
    order = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 4}]},
        headers=user_headers,
    ).json()

    response = client.patch(f"/orders/{order['id']}/cancel", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get(f"/products/{product['id']}").json()["stock"] == 10


def test_status_flow(client, admin_headers, user_headers):
    product = create_product(client, admin_headers)
    order = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
        headers=user_headers,
    ).json()
    url = f"/orders/{order['id']}/status"

    # Skipping a step is not allowed
    response = client.patch(url, json={"status": "shipped"}, headers=admin_headers)
    assert response.status_code == 400

    for status in ("paid", "shipped", "delivered"):
        response = client.patch(url, json={"status": status}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == status


def test_customer_cannot_change_status(client, admin_headers, user_headers):
    product = create_product(client, admin_headers)
    order = client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
        headers=user_headers,
    ).json()
    response = client.patch(
        f"/orders/{order['id']}/status", json={"status": "paid"}, headers=user_headers
    )
    assert response.status_code == 403