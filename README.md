# Stock Management System

A full-stack inventory and order management system. Staff record customer orders, stock is tracked
through an auditable ledger, and access is controlled by user role.

## Tech Stack

- **Frontend:** React 18, TypeScript, Tailwind CSS, Framer Motion (served by nginx)
- **Backend:** Django 4.2, Django REST Framework, JWT authentication (SimpleJWT)
- **Database:** MySQL 8
- **Cache / queue:** Redis 7 (reserved for background jobs)
- **Containers:** Docker Compose

## Features

**Inventory**
- Products with SKU, barcode, category, cost and selling price, and profit margin
- Categories (nested) and suppliers
- Low-stock detection per product (configurable threshold)
- Stock ledger: every stock change is recorded as an append-only movement
  (stock in, stock out, adjustment, return). Movements can't be edited or deleted.

**Orders**
- Staff record orders on behalf of customers (name, email, phone, notes)
- Totals are calculated on the server; product names and prices are saved on each order line,
  so past orders never change when a product is updated
- Placing an order removes stock in a single transaction: if any item lacks stock, nothing is saved
- Status tracking: Pending → Processing → Shipped → Delivered; cancelling returns the stock

**Users & security**
- Email login with JWT access and refresh tokens
- Roles: `admin`, `manager`, `staff`
- Public sign-up always creates `staff` accounts; only admins can grant roles
- Passwords are hashed (PBKDF2) and checked against Django's password validators
- All models are managed in the Django admin

## Project Structure

```
├── backend/                 Django project
│   ├── management/          Project settings (+ settings_test.py), root URLs, middleware
│   ├── users/               Custom user model, roles, auth and profile endpoints
│   ├── inventory/           Categories, products, suppliers, stock ledger (+ services.py)
│   ├── orders/              Orders and order lines (+ services.py)
│   ├── api/                 Login/register views, dashboard, API routing
│   ├── */tests/             Tests for each app (pytest)
│   ├── conftest.py          Shared test fixtures (users per role, API clients)
│   ├── requirements.txt     Runtime dependencies
│   ├── requirements-dev.txt Test tools (pytest, pytest-django, factory_boy)
│   ├── .env.example         Environment template (copy to .env)
│   └── Dockerfile
├── frontend/                React + TypeScript client
│   ├── src/                 Pages, components, auth context, API client
│   ├── nginx.conf           Serves the built app, with client-side routing
│   └── Dockerfile
├── docker/mysql/init/       Runs on a fresh database volume (grants the test database)
├── docs/                    User stories
└── docker-compose.yml       MySQL, Redis, backend and frontend services
```

Business rules live in each app's `services.py` (for example `inventory.services.record_stock_movement`
and `orders.services.place_order`), not in views or model `save()` methods.

## Quick Start (Docker)

You only need [Docker](https://docs.docker.com/get-docker/) with Docker Compose.

1. Clone the repository:
   ```bash
   git clone git@github.com:suca19/Master-Stock-Management-System.git
   cd Master-Stock-Management-System
   ```

2. Create your environment file from the template:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and replace every `change-me` value. The file explains how to generate a
   `SECRET_KEY`. `backend/.env` holds your secrets and is ignored by git: never commit it.

3. Build and start all services:
   ```bash
   docker compose up --build
   ```
   The first run takes a few minutes while MySQL creates its database. Migrations run automatically.

4. Open the app:

   | Service | URL |
   |---|---|
   | Frontend | http://localhost:3000 |
   | API | http://localhost:8000/api/ |
   | Django admin | http://localhost:8000/admin/ |

   Log in with the `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `backend/.env`. That admin account is
   created (or updated) automatically every time the backend starts.

### Useful commands

```bash
docker compose down                        # stop everything (data is kept)
docker compose down -v                     # stop and DELETE the database volume
docker compose logs -f backend             # follow backend logs
docker compose up -d --build frontend      # rebuild the frontend after changes
docker compose exec backend python manage.py makemigrations   # after changing models
docker compose exec db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'   # MySQL shell
```

Backend code is mounted into its container and reloads automatically. Frontend changes need a rebuild.
MySQL (3306) and Redis (6379) are only reachable from your own machine.

## Running Tests

The backend has 133 tests, run with pytest against a real MySQL test database (`test_master_db`),
so database constraints and row locking are tested exactly as they behave in production.

```bash
docker compose exec backend pytest                      # run everything (~25 s)
docker compose exec backend pytest orders               # one app
docker compose exec backend pytest -k cancel            # tests whose name matches "cancel"
docker compose exec backend pytest --create-db          # rebuild the test DB

## Frontend Development

The React app is built inside Docker: `npm install` and `npm run build` run in the image's build stage,
and nginx serves the result. That's why there is no `frontend/node_modules` folder on your machine,
and why frontend changes need a rebuild:

```bash
docker compose up -d --build frontend
```

For autocompletion and type checking in your editor, install the dependencies locally as well
(Node 18+; the folder is ignored by git):

```bash
cd frontend
npm install        # uses package-lock.json, so versions match the Docker build
```

| Route | Page | Access |
|---|---|---|
| `/login`, `/register` | Sign in / sign up | Public |
| `/dashboard` | Overview | Signed in |
| `/inventory` | Products | Signed in |
| `/orders` | Orders | Signed in |
| `/profile` | Profile (admin, manager and staff versions) | Signed in |
| `/admin/*` | Admin area | Admins |
| `/supervisor/*` | Team and reports | Managers and admins |

Login, registration, profiles and user management use the real API. The Inventory and Orders pages
still show sample data; the API endpoints behind them are ready.

## API Overview

All endpoints are under `/api/`, and all except login, register and token refresh require
`Authorization: Bearer <access token>`.

| Endpoint | Description |
|---|---|
| `POST auth/login/` | Get access and refresh tokens (email + password) |
| `POST auth/register/` | Public sign-up (creates a `staff` account) |
| `POST auth/token/refresh/` | Exchange a refresh token for a new access token |
| `POST auth/change-password/` | Change your own password |
| `GET/PATCH users/profile/` | Your own profile |
| `users/` | List users (any signed-in user) · create, delete and change roles (admins) · `users/team-members/` lists active staff |
| `categories/`, `products/`, `suppliers/`, `product-images/` | Inventory CRUD (admins write, staff read) · `products/low_stock/` |
| `stock-movements/` | Stock ledger: list and record movements (append-only) |
| `orders/` | List, create and update orders · `orders/<id>/cancel/` returns stock |
| `GET dashboard/data/` | Product count, low-stock count, total stock value |

List endpoints are paginated (20 per page) and support `?search=` and `?ordering=` where relevant.

## Roles & Permissions

The backend enforces every rule below; the frontend only hides what a role can't use.

| Action | Admin | Manager | Staff |
|---|:---:|:---:|:---:|
| View products, categories, suppliers | ✅ | ❌ ¹ | ✅ |
| Create, edit, delete products, categories, suppliers | ✅ | ❌ | ❌ |
| Record stock movements | ✅ | ✅ | ✅ |
| Create, update and cancel orders | ✅ | ✅ | ✅ |
| View the dashboard | ✅ | ✅ | ✅ |
| Edit own profile, change own password | ✅ | ✅ | ✅ |
| Create or delete users, change roles | ✅ | ❌ | ❌ |

¹ Known issue: managers should be able to view inventory. A test marks it as expected-to-fail until it's fixed.

Nobody can edit or delete stock movements or delete orders: mistakes are corrected with an
adjustment movement, and orders are cancelled instead.
