from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import UserRepository
from app.schemas.schemas import UserListOut, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserListOut)
def list_users(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="page and page_size must be >= 1")
    skip = (page - 1) * page_size
    repo = UserRepository(db)
    users, total = repo.get_all(skip=skip, limit=page_size)
    return UserListOut(total=total, page=page, page_size=page_size, users=users)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
