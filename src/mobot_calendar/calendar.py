from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from icalendar import Calendar, Event

from .models import GardenEvent

LOCATION = "Missouri Botanical Garden\n4344 Shaw Blvd\nSt. Louis, MO 63110"


def build_calendar(events: list[GardenEvent]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//Missouri Botanical Garden Calendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "Missouri Botanical Garden")
    cal.add("x-wr-timezone", "America/Chicago")
    stamp = datetime.now(timezone.utc)
    for item in events:
        event = Event()
        event.add("uid", item.uid)
        event.add("summary", f"🌿 {item.title}")
        if item.all_day:
            event.add("dtstart", date.fromisoformat(item.start_date))
            event.add("dtend", date.fromisoformat(item.end_date) + timedelta(days=1))
        else:
            event.add("dtstart", item.timed_start)
            event.add("dtend", item.timed_end)
        event.add("dtstamp", stamp)
        event.add("location", LOCATION)
        description = []
        if item.daily_hours:
            description.append(f"Daily hours: {item.daily_hours}")
        description.extend(["", item.url])
        event.add("description", "\n".join(description))
        event.add("url", item.url)
        event.add("status", "CANCELLED" if item.status == "cancelled" else "CONFIRMED")
        event.add("sequence", item.missing_count if item.status == "cancelled" else 0)
        cal.add_component(event)
    return cal.to_ical()


def save_calendar(path: Path, events: list[GardenEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_calendar(events))
