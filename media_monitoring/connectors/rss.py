from __future__ import annotations

from datetime import datetime
from typing import Iterable

import feedparser
from dateutil import parser as dt_parser

from media_monitoring.connectors.base import BaseConnector
from media_monitoring.models import ArticleRecord
from media_monitoring.topics import classify_topic


class RSSConnector(BaseConnector):
    feed_urls: tuple[str, ...]
    max_items_per_feed: int

    def __init__(self, max_items_per_feed: int = 150):
        self.max_items_per_feed = max_items_per_feed

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
        for feed_url in self.feed_urls:
            parsed = feedparser.parse(feed_url)
            if getattr(parsed, "bozo", False):
                continue
            entries = getattr(parsed, "entries", [])[: self.max_items_per_feed]
            for entry in entries:
                yield entry

    def fetch(self) -> list[ArticleRecord]:
        articles: list[ArticleRecord] = []
        for entry in self._iter_entries():
            article_url = str(getattr(entry, "link", "")).strip()
            article_title = str(getattr(entry, "title", "")).strip()
            if not article_url or not article_title:
                continue
            tags = self._extract_tags(entry)
            classification = classify_topic(article_title, article_url, tags)
            if classification.topic == "unclassified":
                continue
            articles.append(
                ArticleRecord(
                    outlet=self.outlet,
                    article_url=article_url,
                    article_title=article_title,
                    author_name=self._extract_author(entry),
                    topic=classification.topic,
                    published_at=self._parse_published(getattr(entry, "published", None)),
                    topic_confidence=classification.confidence,
                )
            )
        return articles
