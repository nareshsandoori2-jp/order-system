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
- Order confirmation emails sent in the background (simulated sender, swappable for a real email service)
- Database migrations with Alembic
- Automated tests with pytest on a separate test database, run on every push by GitHub Actions

## Tech stack

Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, PyJWT, pwdlib (Argon2), pytest, Docker, GitHub Actions, Render, Neon

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
│   ├── email_service.py          # simulated order confirmation email
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
   uvicorn app.main:app --reload
   ```

6. Open the interactive API docs at http://127.0.0.1:8000/docs

### Run with Docker

Put `SECRET_KEY=your_long_random_secret` in a `.env` file, then run:

```
docker compose up --build
```

The container applies migrations on start. Open http://127.0.0.1:8000/docs

### Database changes

After editing `models.py`:

```
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Deployment

The API runs on Render (Docker) with a Neon PostgreSQL database. Set these environment variables on the host:

- `DATABASE_URL` (starts with `postgresql+psycopg://`)
- `SECRET_KEY`

The Docker image runs `alembic upgrade head` on start, so new migrations are applied on every deploy.

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
| POST | `/orders` | Logged in | Place an order (sends a confirmation email in the background) |
| GET | `/orders` | Logged in | List your orders |
| GET | `/orders/{id}` | Owner or admin | Get one order |
| PATCH | `/orders/{id}/cancel` | Owner or admin | Cancel a `placed` order |
| PATCH | `/orders/{id}/status` | Admin | Move an order to the next status |
| POST | `/payments` | Owner | Start a payment for a `placed` order |
| POST | `/payments/{id}/simulate-checkout` | Owner | Demo only: stands in for the provider's checkout page |
| POST | `/payments/verify` | Owner | Verify the signature, mark the payment and order `paid` |

## Payment flow

1. `POST /payments` with an `order_id` creates a payment and a provider order ID.
2. `POST /payments/{id}/simulate-checkout` returns a provider payment ID and a signature (this replaces the real checkout page).
3. `POST /payments/verify` with those three values checks the signature. A valid one marks the payment and the order `paid`; an invalid one returns 400.

## Order emails

When an order is placed, FastAPI's `BackgroundTasks` runs `send_order_confirmation` after the response is returned, so the customer does not wait for it. The sender in `app/email_service.py` only writes a log line. To send real emails, replace its body with a call to an email service such as Resend or Brevo.

## Running tests

The tests use the separate `order_system_test` database and never touch your real data.

```
python -m pytest -v
```

## Roadmap

- [x] Alembic database migrations
- [x] GitHub Actions CI
- [x] Docker and Docker Compose
- [x] Payments (simulated provider)
- [x] Deployment
- [x] Move to a database without an expiry (Neon)
- [x] Background order confirmation email (simulated)
- [ ] Real email sending with retries (Resend or Brevo, queue)
- [ ] Real Razorpay test-mode integration