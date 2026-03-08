import httpx

from app.config import settings

PAGE_LIMIT = 100


class ApiClient:

    def __init__(self):
        self.base_url = settings.api_base_url

    def _get_all(self, endpoint: str, key: str) -> list[dict]:
        results = []
        skip = 0
        with httpx.Client(timeout=30) as client:
            while True:
                response = client.get(
                    f"{self.base_url}/{endpoint}",
                    params={"limit": PAGE_LIMIT, "skip": skip}
                )
                response.raise_for_status()
                data = response.json()
                batch = data.get(key, [])
                results.extend(batch)
                skip += PAGE_LIMIT
                if skip >= data.get("total", 0):
                    break
        return results

    def get_users(self) -> list[dict]:
        return self._get_all("users", "users")

    def get_posts(self) -> list[dict]:
        return self._get_all("posts", "posts")

    def get_comments(self) -> list[dict]:
        return self._get_all("comments", "comments")
