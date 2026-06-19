import requests


class InvalidInput(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def is_valid_query(query: str) -> bool:
    return not any(s.isalpha() for s in query)


class APIClient:
    def __init__(self, base_url, headers: dict):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, timeout=5, **kwargs)
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

    def query(self, query: str, results_limit: int = 10):
        if not is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")

        params = {"query": query, "extract": {"count": results_limit}}

        results = self.post("/search", json=params)

        return results


class WikiSearch(APIClient):
    def __init__(
        self,
        base_url: str = "https://en.wikipedia.org/w/rest.php/v1/search",
    ):
        headers = {
            "User-Agent": "MediaWiki REST API docs examples/0.1 (https://www.mediawiki.org/wiki/API_talk:REST_API)"
        }
        super().__init__(base_url, headers)

    def query(self, query: str, result_limit: int = 10):
        if not is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")

        params = {"q": query, "limit": result_limit}

        results = self.get("/page", params=params)

        return results
