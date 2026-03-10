from __future__ import annotations

import json
import re
from html import unescape
from urllib.request import Request, urlopen


META_AUTHOR_PATTERNS = (
    r'<meta[^>]+name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*name=["\']author["\']',
    r'<meta[^>]+property=["\']article:author["\'][^>]*content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']article:author["\']',
    r'<meta[^>]+name=["\']parsely-author["\'][^>]*content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*name=["\']parsely-author["\']',
)


def _clean_author(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = unescape(value).strip()
    cleaned = re.sub(r"^by\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,|-")
    if not cleaned:
        return None
    # Avoid obvious non-byline fragments.
    if len(cleaned) > 120:
        return None
    if "http://" in cleaned or "https://" in cleaned:
        return None
    return cleaned


def _fetch_html(url: str) -> str | None:
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MediaMonitoringBot/0.1; +local-dev)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _extract_author_from_jsonld_obj(obj: object) -> str | None:
    if isinstance(obj, list):
        for item in obj:
            name = _extract_author_from_jsonld_obj(item)
            if name:
                return name
        return None

    if not isinstance(obj, dict):
        return None

    author = obj.get("author")
    if isinstance(author, str):
        return _clean_author(author)

    if isinstance(author, dict):
        name = author.get("name")
        if isinstance(name, str):
            return _clean_author(name)

    if isinstance(author, list):
        names: list[str] = []
        for item in author:
            if isinstance(item, str):
                cleaned = _clean_author(item)
                if cleaned:
                    names.append(cleaned)
            elif isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str):
                    cleaned = _clean_author(name)
                    if cleaned:
                        names.append(cleaned)
        if names:
            return ", ".join(dict.fromkeys(names))

    for value in obj.values():
        name = _extract_author_from_jsonld_obj(value)
        if name:
            return name

    return None


def _extract_author_from_jsonld(html: str) -> str | None:
    scripts = re.findall(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for payload in scripts:
        payload = payload.strip()
        if not payload:
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        author = _extract_author_from_jsonld_obj(obj)
        if author:
            return author
    return None


def extract_author_from_url(url: str) -> str | None:
    html = _fetch_html(url)
    if not html:
        return None

    for pattern in META_AUTHOR_PATTERNS:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            author = _clean_author(match.group(1))
            if author:
                return author

    author = _extract_author_from_jsonld(html)
    if author:
        return author

    # Last-resort byline class/id sniffing.
    fallback = re.search(
        r"<(?:span|p|div)[^>]+(?:class|id)=[\"'][^\"']*(?:author|byline)[^\"']*[\"'][^>]*>(.*?)</(?:span|p|div)>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fallback:
        text = re.sub(r"<[^>]+>", " ", fallback.group(1))
        return _clean_author(text)

    return None
