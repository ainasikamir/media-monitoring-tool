from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class BusinessInsiderConnector(RSSConnector):
    outlet = "Business Insider"
    feed_urls = (
        "https://www.businessinsider.com/rss",
    )
