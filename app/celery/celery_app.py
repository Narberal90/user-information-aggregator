from celery import Celery
from celery.schedules import crontab

from app.config import settings

app = Celery(
    "data_fetcher",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.celery.tasks.user_tasks",
        "app.celery.tasks.post_tasks",
        "app.celery.tasks.comment_tasks",
    ],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
    broker_connection_retry_on_startup=True,
)

app.conf.beat_schedule = {
    "fetch-users": {
        "task": "app.celery.tasks.user_tasks.master_fetch_users_task",
        "schedule": crontab(minute=f"*/{settings.fetch_users_interval}"),
    },
    "fetch-posts": {
        "task": "app.celery.tasks.post_tasks.master_fetch_posts_task",
        "schedule": crontab(minute=f"*/{settings.fetch_posts_interval}"),
    },
    "fetch-comments": {
        "task": "app.celery.tasks.comment_tasks.master_fetch_comments_task",
        "schedule": crontab(minute=f"*/{settings.fetch_comments_interval}"),
    },
}
