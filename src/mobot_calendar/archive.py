from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from .models import GardenEvent


def load_archive(path: Path) -> list[GardenEvent]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [GardenEvent.from_dict(item) for item in data.get("events", [])]


def reconcile(previous: list[GardenEvent], current: list[GardenEvent], *, today: date | None = None) -> list[GardenEvent]:
    today = today or date.today()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    old = {x.identity: x for x in previous}
    fresh = {x.identity: x for x in current}
    result: dict[str, GardenEvent] = {}
    for identity, item in fresh.items():
        item.first_seen = old.get(identity, item).first_seen or now
        item.last_seen = now
        result[identity] = item
    for identity, item in old.items():
        if identity in fresh:
            continue
        if date.fromisoformat(item.end_date) >= today and item.status == "confirmed":
            item.missing_count += 1
            if item.missing_count >= 2:
                item.status = "cancelled"
        result[identity] = item
    return sorted(result.values(), key=lambda x: (x.start_date, x.start_time, x.title))


def save_archive(path: Path, events: list[GardenEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "events": [x.to_dict() for x in events]}, indent=2) + "\n", encoding="utf-8")
