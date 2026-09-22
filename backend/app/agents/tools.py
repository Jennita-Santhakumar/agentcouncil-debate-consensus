"""Module-level LangChain tools.

The PRD's reference implementation defined `@tool`-decorated methods bound to
`self` (`self.retrieve_evidence`) — LangChain's `@tool` decorator produces a
`StructuredTool` from a plain function signature and does not work correctly
bound to an instance. Tools must be module-level functions, so that's what
this module has.

The PRD's evidence tool was an explicitly-labeled mock. This one performs a
real, free web search via the `ddgs` (DuckDuckGo Search) package, no API key
required, with a try/except fallback so a network hiccup never crashes a
debate round.
"""
import logging

from langchain_core.tools import tool

from app.config import get_settings

logger = logging.getLogger(__name__)


@tool
def search_evidence(query: str) -> str:
    """Search the web for evidence/citations relevant to a debate claim.

    Args:
        query: A short, specific search query describing the claim or fact to
            look up evidence for.
    """
    settings = get_settings()
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=settings.max_search_results))
    except Exception as exc:  # network failure, rate limit, etc. must never crash a round
        logger.warning("search_evidence failed for query=%r: %s", query, exc)
        return (
            f"[evidence search unavailable for '{query}': {exc}] "
            "Proceed with the argument using general knowledge and clearly note "
            "that no external citation could be retrieved."
        )

    if not results:
        return f"[no web results found for '{query}']"

    lines = []
    for i, r in enumerate(results, start=1):
        title = r.get("title", "untitled")
        body = r.get("body", "").strip()
        href = r.get("href", "")
        lines.append(f"[{i}] {title} — {body[:300]} (source: {href})")
    return "\n".join(lines)


DEBATE_TOOLS = [search_evidence]
