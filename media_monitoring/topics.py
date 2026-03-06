from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TopicMatch:
    topic: str
    confidence: float


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ai": (
        "artificial intelligence",
        "machine learning",
        "generative ai",
        "llm",
        "openai",
        "anthropic",
        "deepmind",
        "ai model",
        "agentic",
        "neural network",
    ),
    "business": (
        "earnings",
        "revenue",
        "profit",
        "ipo",
        "merger",
        "acquisition",
        "ceo",
        "cfo",
        "market share",
        "supply chain",
    ),
    "tech": (
        "software",
        "hardware",
        "startup",
        "cloud",
        "cybersecurity",
        "chip",
        "semiconductor",
        "platform",
        "app",
        "developer",
    ),
    "politics": (
        "election",
        "congress",
        "senate",
        "white house",
        "policy",
        "campaign",
        "governor",
        "president",
        "parliament",
        "ministry",
    ),
    "health": (
        "health",
        "healthcare",
        "hospital",
        "vaccine",
        "drug",
        "fda",
        "disease",
        "clinical trial",
        "public health",
        "medicare",
    ),
    "breaking_news": (
        "breaking",
        "live updates",
        "just in",
        "urgent",
        "developing story",
        "alert",
    ),
}

URL_HINTS: dict[str, str] = {
    "/technology": "tech",
    "/tech": "tech",
    "/business": "business",
    "/markets": "business",
    "/politics": "politics",
    "/policy": "politics",
    "/health": "health",
    "/ai": "ai",
    "/artificial-intelligence": "ai",
    "/breaking": "breaking_news",
    "/live": "breaking_news",
}


def _count_keyword_matches(text: str, keywords: tuple[str, ...]) -> int:
    count = 0
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            count += 1
    return count


def classify_topic(title: str, url: str, source_tags: list[str] | None = None) -> TopicMatch:
    title_norm = (title or "").strip().lower()
    url_norm = (url or "").strip().lower()
    tags_norm = " ".join((source_tags or [])).lower()
    combined = f"{title_norm} {tags_norm}".strip()

    if not combined and not url_norm:
        return TopicMatch(topic="unclassified", confidence=0.0)

    for hint, topic in URL_HINTS.items():
        if hint in url_norm:
            return TopicMatch(topic=topic, confidence=0.8)

    scores: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = _count_keyword_matches(combined, keywords)
        if score > 0:
            scores[topic] = score

    if not scores:
        return TopicMatch(topic="unclassified", confidence=0.0)

    best_topic = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = min(0.95, scores[best_topic] / max(total, 1))
    return TopicMatch(topic=best_topic, confidence=round(confidence, 2))
