from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/Chicago")


@dataclass(slots=True)
class GardenEvent:
    title: str
    start_date: str
    end_date: str
    start_time: str
    end_time: str
    url: str
    all_day: bool = False
    daily_hours: str | None = None
    status: str = "confirmed"
    first_seen: str | None = None
    last_seen: str | None = None
    missing_count: int = 0

    def __post_init__(self) -> None:
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if end < start:
            raise ValueError("Event end date precedes start date")
        time.fromisoformat(self.start_time)
        time.fromisoformat(self.end_time)
        if self.status not in {"confirmed", "cancelled"}:
            raise ValueError(f"Invalid status: {self.status}")

    @property
    def identity(self) -> str:
        raw = "|".join((self.url.rstrip("/"), self.title, self.start_date, self.end_date, self.start_time, self.end_time))
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    @property
    def uid(self) -> str:
        return f"mobot-{self.identity}@mobot-calendar"

    @property
    def timed_start(self) -> datetime:
        return datetime.combine(date.fromisoformat(self.start_date), time.fromisoformat(self.start_time), TIMEZONE)

    @property
    def timed_end(self) -> datetime:
        result = datetime.combine(date.fromisoformat(self.end_date), time.fromisoformat(self.end_time), TIMEZONE)
        if result <= self.timed_start:
            result += timedelta(days=1)
        return result

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GardenEvent":
        return cls(**value)
