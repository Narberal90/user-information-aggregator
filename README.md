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

| Service | External Port | Description |
|---------|--------------|-------------|
| api | 8000 | FastAPI REST API + Swagger UI |
| worker | — | Celery workers (2 concurrent) |
| beat | — | Celery scheduler |
| flower | 5555 | Celery task monitoring |
| db | — | PostgreSQL 15 (internal only) |
| redis | — | Redis 7 (internal only) |

## Network

Two Docker networks are used:

- **`frontend`** — external-facing services: `api`, `worker`, `beat`, `flower`
- **`backend`** (internal) — isolated from the outside world: `db`, `redis`

`db` and `redis` are never exposed to the host or the internet.

## Quick Start

### Requirements

- Docker
- Docker Compose

### 1. Clone the repository

```bash
git clone <repo-url>
cd user-information-aggregator
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env if you want to change passwords
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

Data will appear in the database automatically after the first Celery Beat trigger (within 20 minutes).

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Health check |
| GET | `/users/` | Paginated list of users |
| GET | `/users/{id}` | User with posts and comments |
| GET | `/posts/` | Paginated list of posts |
| GET | `/posts/{id}` | Post with comments |

### Pagination

```
GET /users/?page=1&page_size=20
GET /posts/?page=2&page_size=10
```

## Task Schedule

| Task | Schedule | Records |
|------|----------|---------|
| Users | every 10 min | 208 |
| Posts | every 15 min | 251 |
| Comments | every 20 min | 340 |

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

## Project Structure

```
app/
├── api/routes/          # FastAPI routes (users, posts)
├── celery/
│   ├── celery_app.py    # Celery config + beat schedule
│   └── tasks/           # user_tasks, post_tasks, comment_tasks
├── db/
│   ├── database.py      # SQLAlchemy engine + session
│   └── repositories.py  # Repository pattern
├── models/models.py     # SQLAlchemy models (User, Post, Comment)
├── schemas/schemas.py   # Pydantic schemas
├── services/
│   └── api_clients.py   # HTTP client for DummyJSON API
├── tests/               # pytest tests
└── main.py              # FastAPI app
alembic/                 # Migration config (versions are generated locally)
.env.example             # Environment variables template
```

## Security

- Containers run as unprivileged `appuser`
- `.env` is not committed to git
- `db` and `redis` are on an internal Docker network — not reachable from outside
- Only `api` (8000) and `flower` (5555) are exposed to the host
