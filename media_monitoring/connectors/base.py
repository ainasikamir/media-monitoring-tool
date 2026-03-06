from __future__ import annotations

from abc import ABC, abstractmethod

from media_monitoring.models import ArticleRecord


class BaseConnector(ABC):
    outlet: str

    @abstractmethod
    def fetch(self) -> list[ArticleRecord]:
        raise NotImplementedError
