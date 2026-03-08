from datetime import datetime

from pydantic import BaseModel

# --- Comment schemas ---

class CommentBase(BaseModel):
    external_id: int
    body: str | None = None

    model_config = {"from_attributes": True}


class CommentOut(CommentBase):
    id: int
    post_id: int | None = None
    user_id: int | None = None
    created_at: datetime


# --- Post schemas ---

class PostBase(BaseModel):
    external_id: int
    title: str | None = None
    body: str | None = None

    model_config = {"from_attributes": True}


class PostOut(PostBase):
    id: int
    user_id: int | None = None
    created_at: datetime
    comments: list[CommentOut] = []


# --- User schemas ---

class UserBase(BaseModel):
    external_id: int
    name: str | None = None
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None

    model_config = {"from_attributes": True}


class UserOut(UserBase):
    id: int
    created_at: datetime
    posts: list[PostOut] = []


class UserListOut(BaseModel):
    total: int
    page: int
    page_size: int
    users: list[UserBase]


class PostListOut(BaseModel):
    total: int
    page: int
    page_size: int
    posts: list[PostOut]
