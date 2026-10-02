# Issue Tracker API

A production-oriented REST API built with FastAPI, PostgreSQL, SQLAlchemy, and
Alembic. It demonstrates a layered backend architecture, JWT authentication,
owner-based authorization, filtering, sorting, pagination, Docker packaging,
and continuous integration.

## Features

- User registration and OAuth2 password login
- Argon2 password hashing and expiring JWT access tokens
- Owner-scoped issue CRUD operations
- Status and priority filters
- Case-insensitive title and description search
- Sorting and offset pagination
- PostgreSQL persistence through SQLAlchemy 2
- Versioned database migrations with Alembic
- Docker Compose development stack
- Ruff, dependency, migration, compilation, and image-build CI checks
- Automatic OpenAPI documentation

## Technology stack

- Python 3.13
- FastAPI and Pydantic
- PostgreSQL 17
- SQLAlchemy 2 and Psycopg 3
- Alembic
- PyJWT and pwdlib with Argon2
- Docker and Docker Compose
- GitHub Actions and Ruff

## Quick start with Docker

Create the environment file and replace the example JWT secret:

```bash
cp .env.example .env
openssl rand -hex 32
```

Paste the generated value into `JWT_SECRET_KEY`, then start the stack:

```bash
docker compose up --build
```

Compose starts PostgreSQL, applies all migrations, and starts the API. Open:

- API documentation: <http://localhost:8000/docs>
- Alternative documentation: <http://localhost:8000/redoc>
- Health endpoint: <http://localhost:8000/api/v1/health>

Stop the services with:

```bash
docker compose down
```

To also remove the development database volume:

```bash
docker compose down --volumes
```

## Local development

Python 3.13 and Docker are required.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d postgres
alembic upgrade head
uvicorn main:app --reload
```

Replace `JWT_SECRET_KEY` in `.env` before starting the API. The default database
URL connects the locally running application to the Compose PostgreSQL port.

## Authentication

Register a user:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"developer@example.com","password":"strong-password"}'
```

Request an access token. OAuth2 calls the email field `username`:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=developer@example.com&password=strong-password'
```

Use the returned token on protected endpoints:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

The **Authorize** button in Swagger UI accepts the same email and password.

## API endpoints

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | No | Application health |
| `POST` | `/api/v1/auth/register` | No | Register a user |
| `POST` | `/api/v1/auth/token` | No | Obtain an access token |
| `GET` | `/api/v1/auth/me` | Bearer | Get the current user |
| `GET` | `/api/v1/issues/` | Bearer | List the current user's issues |
| `POST` | `/api/v1/issues/` | Bearer | Create an issue |
| `GET` | `/api/v1/issues/{issue_id}` | Bearer | Get an owned issue |
| `PATCH` | `/api/v1/issues/{issue_id}` | Bearer | Partially update an owned issue |
| `DELETE` | `/api/v1/issues/{issue_id}` | Bearer | Delete an owned issue |

### Create an issue

```bash
curl -X POST http://localhost:8000/api/v1/issues/ \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Login fails",
    "description": "Users cannot sign in with valid credentials",
    "priority": "high"
  }'
```

New issues start with the `open` status. Supported priorities are `low`,
`medium`, and `high`; supported statuses are `open`, `in_progress`, and
`closed`.

### Filter, sort, search, and paginate

```bash
curl 'http://localhost:8000/api/v1/issues/?status=open&priority=high&search=login&sort_by=updated_at&sort_direction=desc&limit=20&offset=0' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

Available list parameters:

| Parameter | Values | Default |
| --- | --- | --- |
| `status` | `open`, `in_progress`, `closed` | All |
| `priority` | `low`, `medium`, `high` | All |
| `search` | 1–100 characters | None |
| `sort_by` | `created_at`, `updated_at`, `title`, `priority`, `status` | `created_at` |
| `sort_direction` | `asc`, `desc` | `desc` |
| `limit` | 1–100 | 20 |
| `offset` | 0 or greater | 0 |

List responses include pagination metadata:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

For page-number navigation, calculate `offset = (page - 1) * limit` while
keeping filters and sorting unchanged between requests.

## Database migrations

Apply pending migrations:

```bash
alembic upgrade head
```

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe the change"
```

Roll back one migration:

```bash
alembic downgrade -1
```

The Compose `migrate` service applies migrations before the API starts.

## Code quality and CI

Run the local CI checks with:

```bash
ruff check .
ruff format --check .
python -m pip check
python -m compileall -q app migrations main.py
alembic upgrade head --sql > /dev/null
docker build --tag issue-tracker:local .
```

GitHub Actions runs these checks for every push and pull request. The full
automated application test suite is planned as the next project milestone.

## Project layout

```text
app/
├── models/          # SQLAlchemy database models
├── repositories/    # Persistence implementations
├── routes/          # FastAPI HTTP endpoints
├── services/        # Application and business rules
├── config.py        # Environment-backed settings
├── database.py      # Engine and session lifecycle
├── dependencies.py  # Authentication dependencies
├── schema.py        # Issue request/response models
└── security.py      # Password and JWT helpers
migrations/          # Alembic environment and revisions
.github/workflows/   # Continuous integration
Dockerfile           # Production-style API image
compose.yaml         # API, migration, and PostgreSQL services
main.py              # FastAPI application entry point
```

See [Architecture](docs/architecture.md) for component responsibilities,
request flows, data ownership, security boundaries, and design decisions.

## Security notes

- Never use the development JWT secret or database password in production.
- Terminate TLS at a trusted reverse proxy or ingress.
- Restrict CORS origins before exposing the API to browsers.
- Access tokens currently have no refresh or revocation mechanism.
- Requests for another user's issue return `404` to avoid disclosing its
  existence.

## Current roadmap

- Automated unit and integration tests
- Refresh-token rotation and token revocation
- Project membership and role-based permissions
- Structured logging and request IDs
- Production deployment manifests and observability
