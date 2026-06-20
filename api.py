import json

import requests


class InvalidInput(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def is_valid_query(query: str) -> bool:
    return all(s.isdigit() for s in query)


class APIClient:
    def __init__(self, base_url, headers: dict):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()

        return response.json()

    def post(self, endpoint: str, **kwargs) -> dict:
        return self._request("POST", endpoint, **kwargs)

    def get(self, endpoint: str, **kwargs) -> dict:
        return self._request("GET", endpoint, **kwargs)


class KagiSearch(APIClient):
    def __init__(self, api_key: str, base_url: str = "https://kagi.com/api/v1"):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        super().__init__(base_url, headers)

    def query(self, query: str, result_limit: int = 10) -> dict:
        if not is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")

        params = {"query": query, "extract": {"count": result_limit}}

        results = self.post("/search", json=params)

        return results["data"]["search"]


class WikiSearch(APIClient):
    def __init__(
        self,
        base_url: str = "https://en.wikipedia.org/w/rest.php/v1/search",
    ):
        headers = {
            "User-Agent": "MediaWiki REST API docs examples/0.1 (https://www.mediawiki.org/wiki/API_talk:REST_API)"
        }
        super().__init__(base_url, headers)

    def query(self, query: str, result_limit: int = 10) -> dict:
        if not is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")

        params = {"q": query, "limit": result_limit}

        results = self.get("/page", params=params)

        return results


class OEISSearch(APIClient):
    def __init__(self, base_url: str = "https://oeis.org"):
        headers = {"User-Agent": "numbers-db/0.1"}
        super().__init__(base_url, headers)

    def query(self, query: str) -> tuple[list[int], str] | None:
        if not is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")

        params = {"q": query, "fmt": "json"}

        results = self.get("/search", params=params)

        if not results:
            return None

        top = results[0]
        sequence = [int(n) for n in top["data"].split(",")]
        link = f"https://oeis.org/A{top['number']:06d}"

        return sequence, link


class OpenRouter(APIClient):
    def __init__(
        self, api_key: str, base_url: str = "https://openrouter.ai/api/v1/chat"
    ):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-OpenRouter-Title": "numbers-db",  # Optional. Site title for rankings on openrouter.ai.
        }
        super().__init__(base_url, headers)

    def query(self, msg: str) -> dict:
        message = {
            "model": "openai/gpt-oss-20b:free",
            "messages": [{"role": "user", "content": msg}],
            "temperature": 0.0,
            "stream": False,
        }

        response = self.post("/completions", data=json.dumps(message))

        return response
