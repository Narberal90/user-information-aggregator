import logging

from app.celery.celery_app import app
from app.config import settings
from app.db.database import SessionLocal
from app.db.repositories import CommentRepository, PostRepository, UserRepository
from app.services.api_clients import ApiClient

logger = logging.getLogger(__name__)

CHUNK_SIZE = settings.fetch_chunk_size


@app.task(name="app.celery.tasks.comment_tasks.master_fetch_comments_task", bind=True, max_retries=3)
def master_fetch_comments_task(self):

    logger.info("Master comment task: fetching all comments...")
    try:
        client = ApiClient()
        all_comments = client.get_comments()
        total = len(all_comments)
        logger.info(f"Total comments to process: {total}. Chunk size: {CHUNK_SIZE}")

        for i in range(0, total, CHUNK_SIZE):
            chunk = all_comments[i: i + CHUNK_SIZE]
            fetch_comments_chunk_task.delay(comments=chunk)

        logger.info(f"Dispatched {(total // CHUNK_SIZE) + 1} chunk tasks.")
    except Exception as exc:
        logger.error(f"Master comment task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(name="app.celery.tasks.comment_tasks.fetch_comments_chunk_task", bind=True, max_retries=3)
def fetch_comments_chunk_task(self, comments: list[dict]):

    logger.info(f"Processing chunk of {len(comments)} comments...")
    try:
        db = SessionLocal()
        try:
            comment_repo = CommentRepository(db)
            post_repo = PostRepository(db)
            user_repo = UserRepository(db)

            for raw in comments:
                external_post_id = raw.get("postId")
                external_user_id = raw.get("user", {}).get("id")

                post = post_repo.get_by_external_id(external_post_id) if external_post_id else None
                user = user_repo.get_by_external_id(external_user_id) if external_user_id else None

                comment_repo.upsert({
                    "external_id": raw["id"],
                    "post_id": post.id if post else None,
                    "external_post_id": external_post_id,
                    "user_id": user.id if user else None,
                    "external_user_id": external_user_id,
                    "body": raw.get("body"),
                })

            logger.info(f"Chunk of {len(comments)} comments processed.")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Comment chunk task failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
