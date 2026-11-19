![Tests](https://github.com/nareshsandoori2-jp/order-system/actions/workflows/tests.yml/badge.svg)

**Live demo:** https://order-system-m443.onrender.com/docs

A backend API for an online store, built with FastAPI and PostgreSQL. Customers sign up, browse products, place orders and pay for them. Admins manage products and move orders through their status flow.

## Features

- Signup and login with hashed passwords (Argon2) and JWT tokens
- Roles: `customer` and `admin`
- Product management (admin only for create, update, delete)
- Orders with stock checks, automatic stock reduction and totals
- Row locking (`SELECT ... FOR UPDATE`) so two buyers cannot take the last item
- Order cancellation that restores stock
- Order status flow: `placed` -> `paid` -> `shipped` -> `delivered` (invalid jumps are rejected)
- Payments with a simulated provider that signs and verifies payments with HMAC-SHA256, the same way Razorpay does, so the provider can be swapped by replacing one file
- Safe to retry: creating a payment twice for one order returns the same payment, and verifying twice is harmless
- Database migrations with Alembic
- Automated tests with pytest on a separate test database, run on every push by GitHub Actions

## Tech stack

Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, PyJWT, pwdlib (Argon2), pytest, Docker, GitHub Actions, Render

## Project structure

```
order-system/
├── .github/workflows/tests.yml   # CI
├── alembic/                      # database migrations
├── app/
│   ├── main.py                   # app entry point
│   ├── database.py               # database connection
│   ├── models.py                 # database tables
│   ├── schemas.py                # request and response models
│   ├── security.py               # password hashing and JWT
│   ├── deps.py                   # current user and admin checks
│   ├── payment_provider.py       # simulated payment provider
│   └── routers/
│       ├── auth.py               # signup, login
│       ├── products.py           # product endpoints
│       ├── orders.py             # order endpoints
│       └── payments.py           # payment endpoints
├── tests/                        # pytest tests
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
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

4. Create the tables:

   ```
   alembic upgrade head
   ```

5. Start the server:

   ```