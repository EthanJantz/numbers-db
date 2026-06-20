import json
from unittest.mock import MagicMock

import pytest

from api import (
    APIClient,
    InvalidInput,
    KagiSearch,
    OEISSearch,
    OpenRouter,
    SearchClient,
    WikiSearch,
)


def make_response(payload):
    """A stand-in requests.Response that yields `payload` from .json()."""
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    return response


def patch_request(monkeypatch, client, payload):
    """Replace the client's HTTP boundary; return the mock for assertions.

    Mocking ``session.request`` (rather than the client's own get/post) means
    tests assert on the real outgoing request and exercise the actual URL and
    param plumbing in APIClient._request.
    """
    request = MagicMock(return_value=make_response(payload))
    monkeypatch.setattr(client.session, "request", request)
    return request


class DummySearch(SearchClient):
    """Concrete SearchClient so the template behavior can be exercised."""

    def __init__(self):
        super().__init__("https://example.com", {})

    def _search(self, query, *args, **kwargs):
        return {"query": query, "args": args, "kwargs": kwargs}


# --------------------------------------------------------------------------- #
# APIClient
# --------------------------------------------------------------------------- #
class TestAPIClient:
    def test_get_builds_url_and_returns_json(self, monkeypatch):
        client = APIClient("https://example.com", {})
        request = patch_request(monkeypatch, client, {"ok": True})

        result = client.get("/page", params={"q": "42"})

        request.assert_called_once_with(
            "GET", "https://example.com/page", params={"q": "42"}
        )
        assert result == {"ok": True}

    def test_post_uses_post_method(self, monkeypatch):
        client = APIClient("https://example.com", {})
        request = patch_request(monkeypatch, client, {"ok": True})

        client.post("/search", json={"x": 1})

        method, url = request.call_args.args
        assert method == "POST"
        assert url == "https://example.com/search"

    def test_endpoint_leading_slash_is_normalized(self, monkeypatch):
        client = APIClient("https://example.com", {})
        request = patch_request(monkeypatch, client, {})

        client.get("foo")
        client.get("/foo")

        urls = [call.args[1] for call in request.call_args_list]
        assert urls == ["https://example.com/foo", "https://example.com/foo"]

    def test_raise_for_status_is_called(self, monkeypatch):
        client = APIClient("https://example.com", {})
        response = make_response({})
        monkeypatch.setattr(client.session, "request", MagicMock(return_value=response))

        client.get("/foo")

        response.raise_for_status.assert_called_once()


# --------------------------------------------------------------------------- #
# SearchClient (validation + template method)
# --------------------------------------------------------------------------- #
class TestSearchClient:
    @pytest.mark.parametrize(
        "query, expected",
        [
            ("42", True),
            ("0", True),
            ("007", True),
            ("abc", False),
            ("4a2", False),
            ("4.2", False),
            ("-5", False),
            ("12 34", False),
        ],
    )
    def test_is_valid_query(self, query, expected):
        assert SearchClient.is_valid_query(query) is expected

    def test_empty_string_is_invalid(self):
        assert SearchClient.is_valid_query("") is False

    def test_query_forwards_processed_value_and_args(self):
        result = DummySearch().query("42", 5, limit=10)
        assert result == {"query": "42", "args": (5,), "kwargs": {"limit": 10}}

    def test_query_validates_before_searching(self, monkeypatch):
        client = DummySearch()
        search = MagicMock()
        monkeypatch.setattr(client, "_search", search)

        with pytest.raises(InvalidInput):
            client.query("abc")

        search.assert_not_called()

    def test_process_query_returns_value_when_valid(self):
        assert DummySearch()._process_query("42") == "42"

    def test_base_search_is_not_implemented(self):
        client = SearchClient("https://example.com", {})
        with pytest.raises(NotImplementedError):
            client._search("42")


# --------------------------------------------------------------------------- #
# KagiSearch
# --------------------------------------------------------------------------- #
class TestKagiSearch:
    def test_init_sets_auth_header(self):
        client = KagiSearch("secret-key")
        assert client.base_url == "https://kagi.com/api/v1"
        assert client.session.headers["Authorization"] == "Bearer secret-key"

    def test_search_posts_params_and_unwraps_results(self, monkeypatch):
        client = KagiSearch("key")
        request = patch_request(
            monkeypatch, client, {"data": {"search": [{"title": "hit"}]}}
        )

        result = client.query("42", 5)

        request.assert_called_once_with(
            "POST",
            "https://kagi.com/api/v1/search",
            json={"query": "42", "extract": {"count": 5}},
        )
        assert result == [{"title": "hit"}]

    def test_default_result_limit(self, monkeypatch):
        client = KagiSearch("key")
        request = patch_request(monkeypatch, client, {"data": {"search": []}})

        client.query("42")

        assert request.call_args.kwargs["json"]["extract"]["count"] == 10

    def test_invalid_query_raises(self, monkeypatch):
        client = KagiSearch("key")
        request = patch_request(monkeypatch, client, {"data": {"search": []}})
        with pytest.raises(InvalidInput):
            client.query("abc")
        request.assert_not_called()


# --------------------------------------------------------------------------- #
# WikiSearch
# --------------------------------------------------------------------------- #
class TestWikiSearch:
    def test_search_gets_page_with_params(self, monkeypatch):
        client = WikiSearch()
        request = patch_request(monkeypatch, client, {"pages": []})

        result = client.query("42", 3)

        request.assert_called_once_with(
            "GET",
            "https://en.wikipedia.org/w/rest.php/v1/search/page",
            params={"q": "42", "limit": 3},
        )
        assert result == {"pages": []}

    def test_invalid_query_raises(self, monkeypatch):
        client = WikiSearch()
        request = patch_request(monkeypatch, client, {"pages": []})
        with pytest.raises(InvalidInput):
            client.query("abc")
        request.assert_not_called()


# --------------------------------------------------------------------------- #
# OEISSearch
# --------------------------------------------------------------------------- #
class TestOEISSearch:
    def test_search_returns_sequence_and_padded_link(self, monkeypatch):
        client = OEISSearch()
        request = patch_request(
            monkeypatch, client, [{"number": 203, "data": "1,3,4,7,6"}]
        )

        result = client.query("42")

        request.assert_called_once_with(
            "GET", "https://oeis.org/search", params={"q": "42", "fmt": "json"}
        )
        assert result == {
            "query": "42",
            "sequence": [1, 3, 4, 7, 6],
            "link": "https://oeis.org/A000203",
        }

    def test_uses_first_result_only(self, monkeypatch):
        client = OEISSearch()
        patch_request(
            monkeypatch,
            client,
            [
                {"number": 45, "data": "0,1,1,2"},
                {"number": 203, "data": "1,3,4"},
            ],
        )
        result = client.query("42")
        assert result["link"] == "https://oeis.org/A000045"
        assert result["sequence"] == [0, 1, 1, 2]

    @pytest.mark.parametrize("empty", [None, []])
    def test_no_results_returns_none(self, monkeypatch, empty):
        client = OEISSearch()
        patch_request(monkeypatch, client, empty)
        assert client.query("42") is None

    def test_invalid_query_raises(self, monkeypatch):
        client = OEISSearch()
        request = patch_request(monkeypatch, client, [])
        with pytest.raises(InvalidInput):
            client.query("abc")
        request.assert_not_called()


# --------------------------------------------------------------------------- #
# OpenRouter
# --------------------------------------------------------------------------- #
class TestOpenRouter:
    def test_prompt_posts_completion_payload(self, monkeypatch):
        client = OpenRouter("key")
        request = patch_request(monkeypatch, client, {"choices": []})

        result = client.prompt("hello")

        method, url = request.call_args.args
        sent = json.loads(request.call_args.kwargs["data"])
        assert method == "POST"
        assert url == "https://openrouter.ai/api/v1/chat/completions"
        assert sent["messages"] == [{"role": "user", "content": "hello"}]
        assert sent["temperature"] == 0.0
        assert sent["stream"] is False
        assert result == {"choices": []}
