from unittest.mock import MagicMock, patch

import pytest


class TestMasterFetchUsersTask:
    @patch("app.celery.tasks.user_tasks.ApiClient")
    @patch("app.celery.tasks.user_tasks.SessionLocal")
    def test_upserts_all_users(self, mock_session_class, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_users.return_value = [
            {"id": 1, "firstName": "John", "lastName": "Doe", "username": "jdoe", "email": "j@j.com", "phone": "1", "domain": "j.io"},
            {"id": 2, "firstName": "Jane", "lastName": "Smith", "username": "jsmith", "email": "s@s.com", "phone": "2", "domain": "s.io"},
        ]
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db
        mock_repo = MagicMock()

        with patch("app.celery.tasks.user_tasks.UserRepository", return_value=mock_repo):
            from app.celery.tasks.user_tasks import master_fetch_users_task
            master_fetch_users_task()

        assert mock_repo.upsert.call_count == 2

    @patch("app.celery.tasks.user_tasks.ApiClient")
    @patch("app.celery.tasks.user_tasks.SessionLocal")
    def test_name_is_concatenated_correctly(self, mock_session_class, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_users.return_value = [
            {"id": 1, "firstName": "John", "lastName": "Doe", "username": "jdoe", "email": "j@j.com", "phone": "1", "domain": "j.io"},
        ]
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db
        mock_repo = MagicMock()

        with patch("app.celery.tasks.user_tasks.UserRepository", return_value=mock_repo):
            from app.celery.tasks.user_tasks import master_fetch_users_task
            master_fetch_users_task()

        call_data = mock_repo.upsert.call_args[0][0]
        assert call_data["name"] == "John Doe"

    @patch("app.celery.tasks.user_tasks.ApiClient")
    def test_handles_api_failure(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.get_users.side_effect = Exception("API down")

        from app.celery.tasks.user_tasks import master_fetch_users_task
        with pytest.raises(Exception):
            master_fetch_users_task()


class TestMasterFetchPostsTask:
    @patch("app.celery.tasks.post_tasks.fetch_posts_chunk_task")
    @patch("app.celery.tasks.post_tasks.ApiClient")
    def test_dispatches_correct_number_of_chunks(self, mock_client_class, mock_chunk_task):
        mock_client = mock_client_class.return_value
        mock_client.get_posts.return_value = [{"id": i} for i in range(25)]

        with patch("app.celery.tasks.post_tasks.CHUNK_SIZE", 10):
            from app.celery.tasks.post_tasks import master_fetch_posts_task
            master_fetch_posts_task()

        assert mock_chunk_task.delay.call_count == 3

    @patch("app.celery.tasks.post_tasks.fetch_posts_chunk_task")
    @patch("app.celery.tasks.post_tasks.ApiClient")
    def test_saves_post_with_null_user_when_no_match(self, mock_client_class, mock_chunk_task):
        mock_client = mock_client_class.return_value
        mock_client.get_posts.return_value = [{"id": 1, "userId": 99, "title": "Post", "body": ""}]

        mock_chunk_task.delay = MagicMock()

        with patch("app.celery.tasks.post_tasks.CHUNK_SIZE", 10):
            from app.celery.tasks.post_tasks import master_fetch_posts_task
            master_fetch_posts_task()

        chunk = mock_chunk_task.delay.call_args[1]["posts"]
        assert chunk[0]["userId"] == 99

    @patch("app.celery.tasks.post_tasks.SessionLocal")
    def test_chunk_saves_post_with_null_user_when_missing(self, mock_session_class):
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_user_repo = MagicMock()
        mock_user_repo.get_by_external_id.return_value = None

        mock_post_repo = MagicMock()

        with patch("app.celery.tasks.post_tasks.UserRepository", return_value=mock_user_repo):
            with patch("app.celery.tasks.post_tasks.PostRepository", return_value=mock_post_repo):
                from app.celery.tasks.post_tasks import fetch_posts_chunk_task
                fetch_posts_chunk_task(posts=[{"id": 1, "userId": 99, "title": "Orphan", "body": ""}])

        call_data = mock_post_repo.upsert.call_args[0][0]
        assert call_data["user_id"] is None
        assert call_data["external_user_id"] == 99

    @patch("app.celery.tasks.post_tasks.SessionLocal")
    def test_chunk_saves_post_with_user_id_when_user_exists(self, mock_session_class):
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user_repo = MagicMock()
        mock_user_repo.get_by_external_id.return_value = mock_user

        mock_post_repo = MagicMock()

        with patch("app.celery.tasks.post_tasks.UserRepository", return_value=mock_user_repo):
            with patch("app.celery.tasks.post_tasks.PostRepository", return_value=mock_post_repo):
                from app.celery.tasks.post_tasks import fetch_posts_chunk_task
                fetch_posts_chunk_task(posts=[{"id": 1, "userId": 1, "title": "Post", "body": "Body"}])

        call_data = mock_post_repo.upsert.call_args[0][0]
        assert call_data["user_id"] == 10
        assert call_data["external_user_id"] == 1


class TestMasterFetchCommentsTask:
    @patch("app.celery.tasks.comment_tasks.fetch_comments_chunk_task")
    @patch("app.celery.tasks.comment_tasks.ApiClient")
    def test_dispatches_correct_number_of_chunks(self, mock_client_class, mock_chunk_task):
        mock_client = mock_client_class.return_value
        mock_client.get_comments.return_value = [{"id": i} for i in range(35)]

        with patch("app.celery.tasks.comment_tasks.CHUNK_SIZE", 10):
            from app.celery.tasks.comment_tasks import master_fetch_comments_task
            master_fetch_comments_task()

        assert mock_chunk_task.delay.call_count == 4

    @patch("app.celery.tasks.comment_tasks.SessionLocal")
    def test_chunk_saves_comment_with_null_ids_when_missing(self, mock_session_class):
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_post_repo = MagicMock()
        mock_post_repo.get_by_external_id.return_value = None

        mock_user_repo = MagicMock()
        mock_user_repo.get_by_external_id.return_value = None

        mock_comment_repo = MagicMock()

        with patch("app.celery.tasks.comment_tasks.PostRepository", return_value=mock_post_repo):
            with patch("app.celery.tasks.comment_tasks.UserRepository", return_value=mock_user_repo):
                with patch("app.celery.tasks.comment_tasks.CommentRepository", return_value=mock_comment_repo):
                    from app.celery.tasks.comment_tasks import fetch_comments_chunk_task
                    fetch_comments_chunk_task(comments=[{
                        "id": 1,
                        "body": "Nice!",
                        "postId": 242,
                        "user": {"id": 105, "username": "alice"}
                    }])

        call_data = mock_comment_repo.upsert.call_args[0][0]
        assert call_data["post_id"] is None
        assert call_data["user_id"] is None
        assert call_data["external_post_id"] == 242
        assert call_data["external_user_id"] == 105

    @patch("app.celery.tasks.comment_tasks.SessionLocal")
    def test_chunk_saves_comment_with_ids_when_both_exist(self, mock_session_class):
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_post = MagicMock()
        mock_post.id = 18
        mock_post_repo = MagicMock()
        mock_post_repo.get_by_external_id.return_value = mock_post

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user_repo = MagicMock()
        mock_user_repo.get_by_external_id.return_value = mock_user

        mock_comment_repo = MagicMock()

        with patch("app.celery.tasks.comment_tasks.PostRepository", return_value=mock_post_repo):
            with patch("app.celery.tasks.comment_tasks.UserRepository", return_value=mock_user_repo):
                with patch("app.celery.tasks.comment_tasks.CommentRepository", return_value=mock_comment_repo):
                    from app.celery.tasks.comment_tasks import fetch_comments_chunk_task
                    fetch_comments_chunk_task(comments=[{
                        "id": 1,
                        "body": "Nice!",
                        "postId": 242,
                        "user": {"id": 105, "username": "alice"}
                    }])

        call_data = mock_comment_repo.upsert.call_args[0][0]
        assert call_data["post_id"] == 18
        assert call_data["user_id"] == 5
