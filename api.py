import json

import requests


class InvalidInput(Exception):
    def __init__(self, message: str):
        super().__init__(message)


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


class SearchClient(APIClient):
    @staticmethod
    def is_valid_query(query: str) -> bool:
        return all(s.isdigit() for s in query) and len(query) > 0

    def query(self, query: str, *args, **kwargs):
        query = self._process_query(query)
        return self._search(query, *args, **kwargs)

    def _process_query(self, query: str) -> str:
        if not self.is_valid_query(query):
            raise InvalidInput(f"Invalid input: {query}")
        return query

    def _search(self, query: str, *args, **kwargs):
        raise NotImplementedError


class KagiSearch(SearchClient):
    def __init__(self, api_key: str, base_url: str = "https://kagi.com/api/v1"):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        super().__init__(base_url, headers)

    def _search(self, query: str, result_limit: int = 10) -> dict:
        params = {"query": query, "extract": {"count": result_limit}}
        results = self.post("/search", json=params)
        return results["data"]["search"]


class WikiSearch(SearchClient):
    def __init__(
        self,
        base_url: str = "https://en.wikipedia.org/w/rest.php/v1/search",
    ):
        headers = {
            "User-Agent": "MediaWiki REST API docs examples/0.1 (https://www.mediawiki.org/wiki/API_talk:REST_API)"
        }
        super().__init__(base_url, headers)

    def _search(self, query: str, result_limit: int = 10) -> dict:
        params = {"q": query, "limit": result_limit}
        results = self.get("/page", params=params)
        return results


class OEISSearch(SearchClient):
    def __init__(self, base_url: str = "https://oeis.org"):
        headers = {"User-Agent": "numbers-db/0.1"}
        super().__init__(base_url, headers)

    def _search(self, query: str) -> dict[str, str | list[int]] | None:
        params = {"q": query, "fmt": "json"}
        results = self.get("/search", params=params)

        if not results:
            return None

        top = results[0]
        sequence = [int(n) for n in top["data"].split(",")]
        link = f"https://oeis.org/A{top['number']:06d}"

        return {"query": query, "sequence": sequence, "link": link}


class OpenRouter(APIClient):
    def __init__(
        self, api_key: str, base_url: str = "https://openrouter.ai/api/v1/chat"
    ):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-OpenRouter-Title": "numbers-db",  # Optional. Site title for rankings on openrouter.ai.
        }
        super().__init__(base_url, headers)

    def prompt(
        self,
        msg: str,
        system: str | None = None,
        response_format: dict | None = None,
    ) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": msg})

        message = {
            "model": "openai/gpt-oss-20b:free",
            "messages": messages,
            "temperature": 0.0,
            "stream": False,
        }
        if response_format:
            message["response_format"] = response_format

        response = self.post("/completions", data=json.dumps(message))

        return response
