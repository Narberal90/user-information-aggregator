from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import PostRepository
from app.schemas.schemas import PostListOut, PostOut

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=PostListOut)
def list_posts(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="page and page_size must be >= 1")
    skip = (page - 1) * page_size
    repo = PostRepository(db)
    posts, total = repo.get_all(skip=skip, limit=page_size)
    return PostListOut(total=total, page=page, page_size=page_size, posts=posts)


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    repo = PostRepository(db)
    post = repo.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
