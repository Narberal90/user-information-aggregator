from sqlalchemy.orm import Session

from app.models.models import Comment, Post, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int) -> User | None:
        return self.db.query(User).filter(User.external_id == external_id).first()

    def upsert(self, data: dict) -> User:
        user = self.get_by_external_id(data["external_id"])
        if user:
            for key, value in data.items():
                setattr(user, key, value)
        else:
            user = User(**data)
            self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        total = self.db.query(User).count()
        users = self.db.query(User).offset(skip).limit(limit).all()
        return users, total

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int) -> Post | None:
        return self.db.query(Post).filter(Post.external_id == external_id).first()

    def upsert(self, data: dict) -> Post:
        post = self.get_by_external_id(data["external_id"])
        if post:
            for key, value in data.items():
                setattr(post, key, value)
        else:
            post = Post(**data)
            self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Post], int]:
        total = self.db.query(Post).count()
        posts = self.db.query(Post).offset(skip).limit(limit).all()
        return posts, total

    def get_by_id(self, post_id: int) -> Post | None:
        return self.db.query(Post).filter(Post.id == post_id).first()


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int) -> Comment | None:
        return self.db.query(Comment).filter(Comment.external_id == external_id).first()

    def upsert(self, data: dict) -> Comment:
        comment = self.get_by_external_id(data["external_id"])
        if comment:
            for key, value in data.items():
                setattr(comment, key, value)
        else:
            comment = Comment(**data)
            self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment
