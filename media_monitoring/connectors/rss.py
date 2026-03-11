from __future__ import annotations

from datetime import datetime
from typing import Iterable

import feedparser
from dateutil import parser as dt_parser

from media_monitoring.connectors.base import BaseConnector
from media_monitoring.connectors.byline import extract_author_from_url
from media_monitoring.models import ArticleRecord
from media_monitoring.network import fetch_bytes
from media_monitoring.topics import classify_topic


class RSSConnector(BaseConnector):
    feed_urls: tuple[str, ...]
    max_items_per_feed: int
    max_author_lookups: int

    def __init__(self, max_items_per_feed: int = 150, max_author_lookups: int = 40):
        self.max_items_per_feed = max_items_per_feed
        self.max_author_lookups = max_author_lookups

    def _parse_published(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return dt_parser.parse(value)
        except (ValueError, TypeError, OverflowError):
            return None

    def _extract_author(self, entry: feedparser.FeedParserDict) -> str | None:
        author = getattr(entry, "author", None)
        if author:
            return str(author).strip() or None
        authors = getattr(entry, "authors", None)
        if authors and isinstance(authors, list):
            names = [str(a.get("name", "")).strip() for a in authors if isinstance(a, dict)]
            names = [n for n in names if n]
            return ", ".join(names) if names else None
        return None

    def _extract_tags(self, entry: feedparser.FeedParserDict) -> list[str]:
        tags: list[str] = []
        raw_tags = getattr(entry, "tags", None)
        if not raw_tags:
            return tags
        for tag in raw_tags:
            if isinstance(tag, dict):
                term = str(tag.get("term", "")).strip()
                if term:
                    tags.append(term)
        return tags

    def _iter_entries(self) -> Iterable[feedparser.FeedParserDict]:
        def is_feed_payload(payload: bytes) -> bool:
            sample = payload[:2000].lower()
            return b"<rss" in sample or b"<feed" in sample or b"<rdf" in sample

        for feed_url in self.feed_urls:
            try:
                payload = fetch_bytes(
                    feed_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; MediaMonitoringBot/0.1; +local-dev)",
                        "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
                    },
                    timeout=20,
                    validator=is_feed_payload,
                )
                parsed = feedparser.parse(payload)
            except Exception:
                continue
            if getattr(parsed, "bozo", False):
                continue
            entries = getattr(parsed, "entries", [])[: self.max_items_per_feed]
            for entry in entries:
                yield entry

    def fetch(self) -> list[ArticleRecord]:
        articles: list[ArticleRecord] = []
        author_lookups = 0
        for entry in self._iter_entries():
            article_url = str(getattr(entry, "link", "")).strip()
            article_title = str(getattr(entry, "title", "")).strip()
            if not article_url or not article_title:
                continue
            tags = self._extract_tags(entry)
            classification = classify_topic(article_title, article_url, tags)
            if classification.topic == "unclassified":
                continue
            author_name = self._extract_author(entry)
            if not author_name and author_lookups < self.max_author_lookups:
                author_name = extract_author_from_url(article_url)
                author_lookups += 1
            articles.append(
                ArticleRecord(
                    outlet=self.outlet,
                    article_url=article_url,
                    article_title=article_title,
                    author_name=author_name,
                    topic=classification.topic,
                    published_at=self._parse_published(getattr(entry, "published", None)),
                    topic_confidence=classification.confidence,
                )
            )
        return articles
