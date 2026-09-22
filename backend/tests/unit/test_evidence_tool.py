from unittest.mock import patch

from app.agents.tools import search_evidence


def test_search_evidence_returns_fallback_string_on_network_failure():
    with patch("ddgs.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.side_effect = RuntimeError("network unreachable")
        result = search_evidence.invoke({"query": "climate change evidence"})
    assert "unavailable" in result.lower()
    assert "climate change evidence" in result


def test_search_evidence_formats_results():
    fake_results = [
        {"title": "Study A", "body": "Some finding" * 5, "href": "https://example.com/a"},
        {"title": "Study B", "body": "Another finding", "href": "https://example.com/b"},
    ]

    class FakeDDGS:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def text(self, query, max_results=4):
            return fake_results

    with patch("ddgs.DDGS", return_value=FakeDDGS()):
        result = search_evidence.invoke({"query": "test query"})

    assert "Study A" in result
    assert "Study B" in result
    assert "example.com" in result


def test_search_evidence_no_results():
    class FakeDDGS:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def text(self, query, max_results=4):
            return []

    with patch("ddgs.DDGS", return_value=FakeDDGS()):
        result = search_evidence.invoke({"query": "nonexistent nonsense query"})
    assert "no web results" in result.lower()
