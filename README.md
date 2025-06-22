# FastAPI Simple Example

## Description
A very simple FastAPI application with health check and hello endpoints, now with PostgreSQL database support using SQLAlchemy and Alembic for database migrations. Includes a complete JWT-based authentication system.

## Project Structure
```
fast_api_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application
│   ├── auth/
│   │   ├── __init__.py
│   │   └── utils.py         # Authentication utilities
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py    # Database connection setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── item.py          # SQLAlchemy models
│   │   └── user.py          # User model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   ├── database.py      # Database test endpoints
│   │   └── auth.py          # Authentication endpoints
│   └── schemas/
│       ├── __init__.py
│       └── auth.py          # Pydantic schemas
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   ├── env.py              # Alembic environment
│   └── script.py.mako      # Migration template
├── alembic.ini             # Alembic configuration
├── main.py                  # Entry point
├── pyproject.toml
└── README.md
```

## Requirements
- Python 3.9+
- Poetry
- PostgreSQL (running locally or remotely)

## Environment Variables
Set these environment variables to configure the database connection and authentication (defaults are shown):
- POSTGRES_USER (default: postgres)
- POSTGRES_PASSWORD (default: root)
- POSTGRES_HOST (default: localhost)
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB (default: halal_site_db)
- SECRET_KEY (default: your-secret-key-change-in-production)

Example (Windows PowerShell):
```
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="root"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="halal_site_db"
$env:SECRET_KEY="your-super-secret-key-here"
```

## Install dependencies
```
poetry install
```

## Database Setup with Alembic

### Initial Setup (First time only)
```bash
# Run initial migration to create tables
poetry run alembic upgrade head
```

### Working with Migrations

**Create a new migration:**
```bash
# After modifying models, create a new migration
poetry run alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Apply specific migration
poetry run alembic upgrade <revision_id>
```

**Rollback migrations:**
```bash
# Rollback one step
poetry run alembic downgrade -1

# Rollback to specific revision
poetry run alembic downgrade <revision_id>
```

**Check migration status:**
```bash
# Show current migration status
poetry run alembic current

# Show migration history
poetry run alembic history
```

## Run the application
```
poetry run uvicorn main:app --reload
```

## Endpoints

### Health & Database
- `/health` — Returns `{ "status": "ok" }`
- `/hello` — Returns `{ "message": "Hello, world!" }`
- `/db/db-check` — Returns `{ "db_status": "connected" }` if the database connection works

### Authentication
- `POST /auth/register` — Register a new user
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }
  ```

- `POST /auth/login` — Login and get JWT token
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

- `GET /auth/me` — Get current user info (requires Bearer token)

- `POST /auth/logout` — Logout user (requires Bearer token)
  ```json
  {
    "message": "Successfully logged out, this is just a simple logout it doesn't do anything"
  }
  ```

- `POST /auth/password-reset-request` — Request password reset
  ```json
  {
    "email": "user@example.com"
  }
  ```

- `POST /auth/password-reset` — Reset password using token
  ```json
  {
    "token": "reset_token_here",
    "new_password": "newpassword123"
  }
  ```

## API Documentation
Once the server is running, visit:
- http://localhost:8000/docs - Interactive API documentation (Swagger UI)
- http://localhost:8000/redoc - Alternative API documentation (ReDoc)

## Authentication Flow
1. **Register**: Create a new user account
2. **Login**: Get JWT access token
3. **Use Token**: Include `Authorization: Bearer <token>` header for protected endpoints
4. **Password Reset**: Request reset token and use it to set new password

## Security Features
- JWT tokens with 30-minute expiration
- bcrypt password hashing
- Secure password reset tokens (1-hour expiry)
- Email validation
- User account status tracking 