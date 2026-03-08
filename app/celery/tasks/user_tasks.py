import logging

from app.celery.celery_app import app
from app.db.database import SessionLocal
from app.db.repositories import UserRepository
from app.services.api_clients import ApiClient

logger = logging.getLogger(__name__)


@app.task(name="app.celery.tasks.user_tasks.master_fetch_users_task", bind=True, max_retries=3)
def master_fetch_users_task(self):

    logger.info("Starting user fetch task...")
    try:
        client = ApiClient()
        users = client.get_users()
        logger.info(f"Fetched {len(users)} users from API.")

        db = SessionLocal()
        try:
            repo = UserRepository(db)
            for raw in users:
                repo.upsert({
                    "external_id": raw["id"],
                    "name": f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip(),
                    "username": raw.get("username"),
                    "email": raw.get("email"),
                    "phone": raw.get("phone"),
                    "website": raw.get("domain"),
                })
            logger.info(f"Upserted {len(users)} users into DB.")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"User fetch failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
