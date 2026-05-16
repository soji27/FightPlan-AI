"""
WebSearchTool: Searches the web using DuckDuckGo for MMA-related information.
"""

import json
import re
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

# Input validation pattern - allow letters, digits, spaces, and basic punctuation
_ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9\s\.,\?!'\-\(\):éèêëàâùûüîïôœæçÉÈÊËÀÂÙÛÜÎÏÔŒÆÇ]+$")
_MAX_QUERY_LENGTH = 500


def _validate_query(query: str) -> str:
    """Validate and sanitize a search query.

    Args:
        query: Raw query string.

    Returns:
        Stripped and validated query.

    Raises:
        ValueError: If query is too long or contains invalid characters.
    """
    query = query.strip()
    if len(query) > _MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long ({len(query)} > {_MAX_QUERY_LENGTH} chars)")
    if not _ALLOWED_PATTERN.match(query):
        raise ValueError(f"Query contains invalid characters: '{query}'")
    return query


class WebSearchTool:
    """MMA-focused web search tool powered by DuckDuckGo."""

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web and return a list of result dicts.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return (default 5).

        Returns:
            List of {"title": str, "url": str, "snippet": str} dicts.
            Returns empty list on error.
        """
        try:
            validated_query = _validate_query(query)
        except ValueError as e:
            print(f"[Outil] web_search validation error: {e}")
            return []

        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(validated_query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("url", "")),
                        "snippet": r.get("body", r.get("snippet", "")),
                    })

            print(f"[Outil] web_search appelé → résultat brut: {json.dumps(results, ensure_ascii=False)}")
            return results

        except ImportError:
            print("[Outil] web_search ERROR: duckduckgo_search not installed")
            return []
        except Exception as exc:
            print(f"[Outil] web_search ERROR: {exc}")
            return []

    def search_mma(self, query: str) -> str:
        """Search for MMA-specific information and return a formatted string.

        Args:
            query: MMA-related search query.

        Returns:
            Formatted string with search results, or error message.
        """
        mma_query = f"MMA UFC {query}"
        results = self.search(mma_query, max_results=5)

        if not results:
            return f"No web results found for: {query}"

        lines = [f"Web search results for '{query}':"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet'][:300]}")
            if r.get("url"):
                lines.append(f"   Source: {r['url']}")
            lines.append("")

        formatted = "\n".join(lines)
        print(f"[Outil] web_search appelé → résultat brut: {json.dumps({'query': query, 'formatted_length': len(formatted)}, ensure_ascii=False)}")
        return formatted
