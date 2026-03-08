from fastapi import Depends, FastAPI

from app.api.dependencies import verify_api_key
from app.api.routes import posts, users

app = FastAPI(
    title="User_Information_Aggregator",
    description="Periodically fetches users, posts, and comments from public APIs via Celery.",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)],
)

app.include_router(users.router)
app.include_router(posts.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "docs": "/docs"}
