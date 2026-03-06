from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class WiredConnector(RSSConnector):
    outlet = "Wired"
    feed_urls = (
        "https://www.wired.com/feed/rss",
    )
