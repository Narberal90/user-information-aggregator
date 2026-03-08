from app.db.repositories import PostRepository, UserRepository


class TestUsersAPI:
    def test_list_users_empty(self, client):
        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["users"] == []

    def test_list_users_with_data(self, client, db):
        repo = UserRepository(db)
        repo.upsert({"external_id": 1, "name": "IronMan", "email": "ironman@stark.com"})
        repo.upsert({"external_id": 2, "name": "Kirito", "email": "kirito@sao.com"})

        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["users"]) == 2

    def test_list_users_pagination(self, client, db):
        repo = UserRepository(db)
        for i in range(5):
            repo.upsert({"external_id": i + 1, "name": f"User {i + 1}"})

        response = client.get("/users/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["users"]) == 2
        assert data["page"] == 1

    def test_get_user_not_found(self, client):
        response = client.get("/users/9999")
        assert response.status_code == 404

    def test_get_user_by_id(self, client, db):
        repo = UserRepository(db)
        user = repo.upsert({"external_id": 1, "name": "IronMan"})

        response = client.get(f"/users/{user.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "IronMan"

    def test_invalid_pagination_params(self, client):
        response = client.get("/users/?page=0&page_size=10")
        assert response.status_code == 400


class TestPostsAPI:
    def _create_user_and_post(self, db):
        user_repo = UserRepository(db)
        user = user_repo.upsert({"external_id": 1, "name": "Kirito"})
        post_repo = PostRepository(db)
        post = post_repo.upsert({"external_id": 1, "user_id": user.id, "title": "Test Post", "body": "Body"})
        return user, post

    def test_list_posts_empty(self, client):
        response = client.get("/posts/")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_posts_with_data(self, client, db):
        self._create_user_and_post(db)
        response = client.get("/posts/")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_get_post_not_found(self, client):
        response = client.get("/posts/9999")
        assert response.status_code == 404

    def test_get_post_by_id(self, client, db):
        _, post = self._create_user_and_post(db)
        response = client.get(f"/posts/{post.id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Post"
