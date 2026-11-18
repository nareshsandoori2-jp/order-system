# Order System
![Tests](https://github.com/nareshsandoori2-jp/order-system/actions/workflows/tests.yml/badge.svg)

**Live demo:** https://order-system-m443.onrender.com/docs

A backend API for an online store, built with FastAPI and PostgreSQL. Customers sign up, browse products and place orders. Admins manage products and move orders through their status flow.

## Features

- Signup and login with hashed passwords (Argon2) and JWT tokens
- Roles: `customer` and `admin`
- Product management (admin only for create, update, delete)
- Orders with stock checks, automatic stock reduction and totals
- Row locking (`SELECT ... FOR UPDATE`) so two buyers cannot take the last item
- Order cancellation that restores stock
- Order status flow: `placed` -> `paid` -> `shipped` -> `delivered` (invalid jumps are rejected)
- Automated tests with pytest on a separate test database

## Tech stack

Python, FastAPI, PostgreSQL, SQLAlchemy, PyJWT, pwdlib (Argon2), pytest

## Project structure

```
order-system/
├── app/
│   ├── main.py          # app entry point
│   ├── database.py      # database connection
│   ├── models.py        # database tables
│   ├── schemas.py       # request and response models
│   ├── security.py      # password hashing and JWT
│   ├── deps.py          # current user and admin checks
│   └── routers/
│       ├── auth.py      # signup, login
│       ├── products.py  # product endpoints
│       └── orders.py    # order endpoints
├── tests/               # pytest tests
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository and create a virtual environment:

   ```
   git clone https://github.com/nareshsandoori2-jp/order-system.git
   cd order-system
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create two PostgreSQL databases: `order_system` and `order_system_test`.

3. Create a `.env` file in the project root:

   ```
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/order_system
   SECRET_KEY=your_long_random_secret
   TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/order_system_test
   ```

   Generate a secret key with:

   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Start the server:

   ```
   uvicorn app.main:app --reload
   ```

5. Open the interactive API docs at http://127.0.0.1:8000/docs


### Run with Docker

Put `SECRET_KEY=your_long_random_secret` in a `.env` file, then run:

```
docker compose up --build
```

Open http://127.0.0.1:8000/docs

## API endpoints

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/signup` | Public | Create an account |
| POST | `/auth/login` | Public | Get a JWT token |
| GET | `/products` | Public | List products |
| GET | `/products/{id}` | Public | Get one product |
| POST | `/products` | Admin | Create a product |
| PUT | `/products/{id}` | Admin | Update a product |
| DELETE | `/products/{id}` | Admin | Delete a product |
| POST | `/orders` | Logged in | Place an order |
| GET | `/orders` | Logged in | List your orders |
| GET | `/orders/{id}` | Owner or admin | Get one order |
| PATCH | `/orders/{id}/cancel` | Owner or admin | Cancel a `placed` order |
| PATCH | `/orders/{id}/status` | Admin | Move an order to the next status |

## Running tests

The tests use the separate `order_system_test` database and never touch your real data.

```
python -m pytest -v
```

## Roadmap

- [ ] Alembic database migrations
- [x] GitHub Actions CI
- [x] Docker and Docker Compose
- [ ] Razorpay test payments
- [ ] Background jobs for order emails
- [x] Deployment