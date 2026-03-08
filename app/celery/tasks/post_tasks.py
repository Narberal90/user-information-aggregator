import logging

from app.celery.celery_app import app
from app.config import settings
from app.db.database import SessionLocal
from app.db.repositories import PostRepository, UserRepository
from app.services.api_clients import ApiClient

logger = logging.getLogger(__name__)

CHUNK_SIZE = settings.fetch_chunk_size


@app.task(name="app.celery.tasks.post_tasks.master_fetch_posts_task", bind=True, max_retries=3)
def master_fetch_posts_task(self):

    logger.info("Master post task: fetching all posts...")
    try:
        client = ApiClient()
        all_posts = client.get_posts()
        total = len(all_posts)
        logger.info(f"Total posts to process: {total}. Chunk size: {CHUNK_SIZE}")

        for i in range(0, total, CHUNK_SIZE):
            chunk = all_posts[i: i + CHUNK_SIZE]
            fetch_posts_chunk_task.delay(posts=chunk)

        logger.info(f"Dispatched {(total // CHUNK_SIZE) + 1} chunk tasks.")
    except Exception as exc:
        logger.error(f"Master post task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(name="app.celery.tasks.post_tasks.fetch_posts_chunk_task", bind=True, max_retries=3)
def fetch_posts_chunk_task(self, posts: list[dict]):

    logger.info(f"Processing chunk of {len(posts)} posts...")
    try:
        db = SessionLocal()
        try:
            post_repo = PostRepository(db)
            user_repo = UserRepository(db)

            for raw in posts:
                external_user_id = raw.get("userId", 0)
                user = user_repo.get_by_external_id(external_user_id)

                post_repo.upsert({
                    "external_id": raw["id"],
                    "user_id": user.id if user else None,
                    "external_user_id": external_user_id,
                    "title": raw.get("title", ""),
                    "body": raw.get("body", ""),
                })

            logger.info(f"Chunk of {len(posts)} posts processed.")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Post chunk task failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
