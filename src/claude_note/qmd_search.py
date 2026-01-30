"""
QMD semantic search integration for claude-note.

Provides semantic search capabilities using the qmd MCP tool if available.
Falls back gracefully if qmd is not available.
"""

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SearchResult:
    """A semantic search result."""
    path: str
    title: str
    score: float
    snippet: str = ""


def is_qmd_available() -> bool:
    """Check if qmd command-line tool is available."""
    try:
        result = subprocess.run(
            ["qmd", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def search_vector(
    query: str,
    limit: int = 10,
    min_score: float = 0.3,
) -> list[SearchResult]:
    """
    Perform semantic (vector) search using qmd vsearch.

    Args:
        query: Natural language query
        limit: Maximum results to return
        min_score: Minimum similarity score (0-1)

    Returns:
        List of SearchResult objects
    """
    if not is_qmd_available():
        return []

    try:
        result = subprocess.run(
            [
                "qmd", "vsearch",
                query,
                "--limit", str(limit),
                "--min-score", str(min_score),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        results = []

        for item in data.get("results", []):
            results.append(SearchResult(
                path=item.get("path", ""),
                title=item.get("title", Path(item.get("path", "")).stem),
                score=float(item.get("score", 0)),
                snippet=item.get("snippet", ""),
            ))

        return results

    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        return []


def search_keyword(
    query: str,
    limit: int = 10,
) -> list[SearchResult]:
    """
    Perform keyword (BM25) search using qmd search.

    Args:
        query: Keywords to search for
        limit: Maximum results to return

    Returns:
        List of SearchResult objects
    """
    if not is_qmd_available():
        return []

    try:
        result = subprocess.run(
            [
                "qmd", "search",
                query,
                "--limit", str(limit),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        results = []

        for item in data.get("results", []):
            results.append(SearchResult(
                path=item.get("path", ""),
                title=item.get("title", Path(item.get("path", "")).stem),
                score=float(item.get("score", 0)),
                snippet=item.get("snippet", ""),
            ))

        return results

    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        return []


def find_similar_content(
    query: str,
    limit: int = 5,
    min_score: float = 0.6,
) -> list[SearchResult]:
    """
    Find content semantically similar to the given query.

    Used for deduplication checking.

    Args:
        query: Content to find similar matches for
        limit: Maximum results
        min_score: Minimum similarity threshold

    Returns:
        List of SearchResult objects sorted by score descending
    """
    return search_vector(query, limit=limit, min_score=min_score)


def find_related_notes(
    keywords: list[str] = None,
    tags: list[str] = None,
    limit: int = 10,
    use_semantic: bool = True,
) -> list[SearchResult]:
    """
    Find notes related to keywords and tags.

    Combines keyword and semantic search for best results.

    Args:
        keywords: Keywords to search for
        tags: Tags to match (used as additional keywords)
        limit: Maximum results
        use_semantic: Use vector search (slower but better)

    Returns:
        List of SearchResult objects
    """
    if not is_qmd_available():
        return []

    # Build query from keywords and tags
    query_parts = []
    if keywords:
        query_parts.extend(keywords)
    if tags:
        # Tags are often descriptive, include them
        query_parts.extend(tags)

    if not query_parts:
        return []

    query = " ".join(query_parts)

    if use_semantic:
        return search_vector(query, limit=limit)
    else:
        return search_keyword(query, limit=limit)


def get_document(file_path: str) -> Optional[str]:
    """
    Get the full content of a document by path.

    Args:
        file_path: Path to the document (relative or absolute)

    Returns:
        Document content, or None if not found
    """
    if not is_qmd_available():
        return None

    try:
        result = subprocess.run(
            ["qmd", "get", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return None

        return result.stdout

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
