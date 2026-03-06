from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class FortuneConnector(RSSConnector):
    outlet = "Fortune"
    feed_urls = (
        "https://fortune.com/feed/",
    )
