from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.memory.store import MemoryStore

_ALLOWED_SCHEMES = {"http", "https"}


class DataSource(ABC):
    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class FileDataSource(DataSource):
    def __init__(self, path: str) -> None:
        self.path = path

    def fetch(self) -> list[dict[str, Any]]:
        if self.path.endswith(".csv"):
            with open(self.path, newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))

        with open(self.path, encoding="utf-8") as handle:
            content = handle.read().strip()

        if not content:
            return []

        if self.path.endswith(".jsonl"):
            return [json.loads(line) for line in content.splitlines() if line.strip()]

        if content.startswith("{") and "\n" in content:
            records: list[dict[str, Any]] = []
            for line in content.splitlines():
                line = line.strip()
                if line:
                    records.append(json.loads(line))
            return records

        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        return [parsed]


class HttpDataSource(DataSource):
    def __init__(self, url: str, headers: dict[str, str] | None = None, timeout: int = 10) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed; use http or https.")
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout

    def fetch(self) -> list[dict[str, Any]]:
        request = Request(self.url, headers=self.headers)  # noqa: S310 - scheme validated in __init__
        with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, list):
            return data
        return [data]


class DataQualityValidator:
    def __init__(self) -> None:
        self._required_fields: list[str] = []

    def required_fields(self, fields: list[str]) -> DataQualityValidator:
        self._required_fields = list(fields)
        return self

    def score(self, record: dict[str, Any]) -> float:
        if not record:
            return 0.0
        values = list(record.values())
        non_empty = sum(1 for value in values if value not in (None, "", [], {}))
        return non_empty / len(values)

    def validate(self, record: dict[str, Any], min_score: float = 0.5) -> bool:
        for field in self._required_fields:
            if field not in record:
                return False
        return self.score(record) >= min_score


class IngestionPipeline:
    def __init__(
        self,
        sources: list[DataSource],
        memory: MemoryStore,
        validator: DataQualityValidator | None = None,
    ) -> None:
        self.sources = sources
        self.memory = memory
        self.validator = validator

    def run(self) -> dict[str, Any]:
        ingested = 0
        rejected = 0
        for source in self.sources:
            try:
                records = source.fetch()
            except Exception:
                continue
            for record in records:
                if self.validator and not self.validator.validate(record):
                    rejected += 1
                    continue
                self.memory.write("ingested_record", record)
                ingested += 1
        return {"ingested": ingested, "rejected": rejected}
