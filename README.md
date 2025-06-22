# FastAPI Simple Example

## Description
A very simple FastAPI application with health check and hello endpoints, now with PostgreSQL database support using SQLAlchemy and Alembic for database migrations.

## Project Structure
```
fast_api_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py    # Database connection setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py          # SQLAlchemy models
│   └── routers/
│       ├── __init__.py
│       ├── health.py        # Health check endpoints
│       └── database.py      # Database test endpoints
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
Set these environment variables to configure the database connection (defaults are shown):
- POSTGRES_USER (default: postgres)
- POSTGRES_PASSWORD (default: root)
- POSTGRES_HOST (default: localhost)
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB (default: halal_site_db)

Example (Windows PowerShell):
```
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="root"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="halal_site_db"
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
- `/health` — Returns `{ "status": "ok" }`
- `/hello` — Returns `{ "message": "Hello, world!" }`
- `/db/db-check` — Returns `{ "db_status": "connected" }` if the database connection works

## API Documentation
Once the server is running, visit:
- http://localhost:8000/docs - Interactive API documentation (Swagger UI)
- http://localhost:8000/redoc - Alternative API documentation (ReDoc) 