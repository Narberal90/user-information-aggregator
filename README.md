# User Information Aggregator

A service that periodically collects data about users, posts, and comments from [DummyJSON](https://dummyjson.com) and stores it in PostgreSQL.

## Stack

- **FastAPI** — REST API
- **Celery + Redis** — background tasks and queue
- **Celery Beat** — task scheduler
- **Flower** — Celery task monitoring
- **PostgreSQL** — database
- **Alembic** — database migrations
- **Docker + Docker Compose** — containerization

## Architecture

```
Celery Beat (scheduler)
      │
      ▼
   Redis (queue)
      │
      ▼
Master Task ──► fan-out ──► Chunk Tasks (parallel)
                                  │
                                  ▼
                             PostgreSQL
```

**Fan-out pattern**: a master task fetches all data from the API, splits it into chunks and dispatches them to the queue — workers process them in parallel.

**Eventual consistency**: if a comment arrives before its post — it is saved with `post_id=NULL` and `external_post_id`. On the next task run, upsert automatically fills in the relationship.

## Services

| Service | External Port | Description                   |
| ------- | ------------- | ----------------------------- |
| api     | 8000          | FastAPI REST API + Swagger UI |
| worker  | —             | Celery workers (2 concurrent) |
| beat    | —             | Celery scheduler              |
| flower  | 5555          | Celery task monitoring        |
| db      | —             | PostgreSQL 15 (internal only) |
| redis   | —             | Redis 7 (internal only)       |

## Network

Two Docker networks are used:

- **`frontend`** — external-facing services: `api`, `worker`, `beat`, `flower`
- **`backend`** (internal) — isolated from the outside world: `db`, `redis`

`db` and `redis` are never exposed to the host or the internet.

## Authentication

All API endpoints are protected with an API key. Pass it in the request header:

```
X-API-Key: your-secret-api-key
```

Example:

```bash
curl -H "X-API-Key: your-secret-api-key" http://localhost:8000/users/
```

Without a valid key the API returns `401 Unauthorized`.

## Quick Start

### Requirements

- Docker
- Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/Narberal90/user-information-aggregator.git

cd user-information-aggregator
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env — set a strong API_KEY and change passwords
```

### 3. Build images

```bash
docker compose build
```

### 4. Generate migration

```bash
docker compose run --rm migrate alembic revision --autogenerate -m "initial"
```

### 5. Start

```bash
docker compose up -d
```

### 6. Verify

- **Swagger UI**: http://localhost:8000/docs
- **Flower**: http://localhost:5555

---

Data will appear in the database automatically after the first Celery Beat trigger (within 20 minutes), or you can change the relevant keys in the .env file before building Docker for faster results.

## API Endpoints

All endpoints require `X-API-Key` header.

| Method | URL           | Description                  |
| ------ | ------------- | ---------------------------- |
| GET    | `/`           | Health check                 |
| GET    | `/users/`     | Paginated list of users      |
| GET    | `/users/{id}` | User with posts and comments |
| GET    | `/posts/`     | Paginated list of posts      |
| GET    | `/posts/{id}` | Post with comments           |

### Pagination

```
GET /users/?page=1&page_size=20
GET /posts/?page=2&page_size=10
```

## Task Schedule

Configurable via `.env`:

| Task     | Variable                  | Default |
| -------- | ------------------------- | ------- |
| Users    | `FETCH_USERS_INTERVAL`    | 10 min  |
| Posts    | `FETCH_POSTS_INTERVAL`    | 15 min  |
| Comments | `FETCH_COMMENTS_INTERVAL` | 20 min  |

## Tests & Linter

```bash
# Create venv (requires Python 3.12)
uv venv --python 3.12
source .venv/bin/activate

# Install dev dependencies
uv pip install -r requirements-test.txt

# Run tests
pytest

# Linter
ruff check app/
ruff check app/ --fix
```

## Changing DB Models

After any change to `app/models/models.py`:

```bash
docker compose down
docker compose run --rm migrate alembic revision --autogenerate -m "describe changes"
docker compose up -d
```

## Useful Commands

```bash
# Logs for a specific service
docker compose logs -f worker

# Container status
docker compose ps

# Resource usage
docker stats --no-stream

# Connect to the database
docker exec -it user-information-aggregator-db-1 psql -U user -d mydb

# Check record counts
docker exec -it user-information-aggregator-db-1 psql -U user -d mydb -c "
  SELECT
    (SELECT COUNT(*) FROM users) AS users,
    (SELECT COUNT(*) FROM posts) AS posts,
    (SELECT COUNT(*) FROM comments) AS comments;
"

# Current migration version
docker compose run --rm migrate alembic current

# Stop and remove all data
docker compose down -v
```

## Security

- Containers run as unprivileged `appuser`
- All API endpoints protected with API key (`X-API-Key` header)
- `db` and `redis` are on an internal Docker network — not reachable from outside
- Only `api` (8000) and `flower` (5555) are exposed to the host

## Live Demo (Deployed on AWS)

The service is running on an AWS EC2 instance. Access via the browser:

- **Swagger UI (API Docs)**: http://18.197.155.34:8000/docs
- **Flower (Celery Task Monitoring)**: http://18.197.155.34:5555

_(To interact with the API via Swagger UI, you will need to click "Authorize" and provide the valid `X-API-Key`)._
