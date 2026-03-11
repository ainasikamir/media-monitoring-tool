from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ALLOWED_TOPICS = {
    "sxsw",
    "ai",
    "business",
    "tech",
    "politics",
    "health",
    "breaking_news",
    "unclassified",
}


@dataclass(slots=True)
class ArticleRecord:
    outlet: str
    article_url: str
    article_title: str
    author_name: str | None
    topic: str
    published_at: datetime | None
    topic_confidence: float

    def __post_init__(self) -> None:
        if self.topic not in ALLOWED_TOPICS:
            raise ValueError(f"Unsupported topic: {self.topic}")
