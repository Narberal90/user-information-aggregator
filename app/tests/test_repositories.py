from app.db.repositories import CommentRepository, PostRepository, UserRepository


class TestUserRepository:
    def test_upsert_creates_new_user(self, db):
        repo = UserRepository(db)
        user = repo.upsert({
            "external_id": 1,
            "name": "IronMan",
            "email": "ironman@stark.com",
            "username": "ironman",
            "phone": "123",
            "website": "stark.io",
        })
        assert user.id is not None
        assert user.name == "IronMan"
        assert user.external_id == 1

    def test_upsert_updates_existing_user(self, db):
        repo = UserRepository(db)
        repo.upsert({"external_id": 1, "name": "IronMan", "email": "old@stark.com"})
        updated = repo.upsert({"external_id": 1, "name": "IronMan Updated", "email": "new@stark.com"})
        assert updated.name == "IronMan Updated"
        assert updated.email == "new@stark.com"

    def test_get_by_external_id_returns_none_for_missing(self, db):
        repo = UserRepository(db)
        result = repo.get_by_external_id(999)
        assert result is None

    def test_get_all_returns_paginated_results(self, db):
        repo = UserRepository(db)
        for i in range(5):
            repo.upsert({"external_id": i + 1, "name": f"User {i + 1}"})

        users, total = repo.get_all(skip=0, limit=3)
        assert total == 5
        assert len(users) == 3

    def test_get_by_id_returns_correct_user(self, db):
        repo = UserRepository(db)
        created = repo.upsert({"external_id": 42, "name": "Kirito"})
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "Kirito"


class TestPostRepository:
    def _create_user(self, db):
        return UserRepository(db).upsert({"external_id": 1, "name": "IronMan"})

    def test_upsert_creates_new_post(self, db):
        user = self._create_user(db)
        repo = PostRepository(db)
        post = repo.upsert({"external_id": 101, "user_id": user.id, "title": "Hello", "body": "World"})
        assert post.id is not None
        assert post.title == "Hello"
        assert post.user_id == user.id

    def test_upsert_updates_existing_post(self, db):
        user = self._create_user(db)
        repo = PostRepository(db)
        repo.upsert({"external_id": 101, "user_id": user.id, "title": "Old Title", "body": ""})
        updated = repo.upsert({"external_id": 101, "user_id": user.id, "title": "New Title", "body": ""})
        assert updated.title == "New Title"

    def test_upsert_creates_post_with_null_user(self, db):
        repo = PostRepository(db)
        post = repo.upsert({"external_id": 101, "user_id": None, "external_user_id": 99, "title": "Orphan", "body": ""})
        assert post.user_id is None
        assert post.external_user_id == 99

    def test_get_all_returns_correct_total(self, db):
        user = self._create_user(db)
        repo = PostRepository(db)
        for i in range(4):
            repo.upsert({"external_id": i + 1, "user_id": user.id, "title": f"Post {i}", "body": ""})
        posts, total = repo.get_all(skip=0, limit=10)
        assert total == 4
        assert len(posts) == 4

    def test_get_by_id_returns_correct_post(self, db):
        user = self._create_user(db)
        repo = PostRepository(db)
        created = repo.upsert({"external_id": 1, "user_id": user.id, "title": "Test", "body": ""})
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.title == "Test"


class TestCommentRepository:
    def _create_post(self, db):
        user = UserRepository(db).upsert({"external_id": 1, "name": "Kirito"})
        return PostRepository(db).upsert({"external_id": 1, "user_id": user.id, "title": "Post", "body": ""})

    def test_upsert_creates_comment(self, db):
        post = self._create_post(db)
        repo = CommentRepository(db)
        comment = repo.upsert({
            "external_id": 1,
            "post_id": post.id,
            "external_post_id": 1,
            "body": "Nice post!",
        })
        assert comment.id is not None
        assert comment.body == "Nice post!"
        assert comment.post_id == post.id

    def test_upsert_updates_comment(self, db):
        post = self._create_post(db)
        repo = CommentRepository(db)
        repo.upsert({"external_id": 1, "post_id": post.id, "body": "Old"})
        updated = repo.upsert({"external_id": 1, "post_id": post.id, "body": "New"})
        assert updated.body == "New"

    def test_upsert_creates_comment_with_null_post(self, db):
        repo = CommentRepository(db)
        comment = repo.upsert({
            "external_id": 1,
            "post_id": None,
            "external_post_id": 242,
            "body": "Orphan comment",
        })
        assert comment.post_id is None
        assert comment.external_post_id == 242
