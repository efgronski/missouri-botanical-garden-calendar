from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import GardenEvent

LOG = logging.getLogger(__name__)
CALENDAR_URL = "https://www.missouribotanicalgarden.org/events-classes/calendar"
TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", re.I)


class ScrapeError(RuntimeError):
    pass


def _parse_date(node) -> str:
    text = " ".join(x.get_text(" ", strip=True) for x in node.select(".date-month, .date-day, .date-year"))
    return datetime.strptime(text, "%B %d %Y").date().isoformat()


def _parse_clock(value: str) -> str:
    return datetime.strptime(" ".join(value.upper().split()), "%I:%M %p").time().strftime("%H:%M")


def parse_calendar(page: str) -> list[GardenEvent]:
    soup = BeautifulSoup(page, "html.parser")
    events: dict[str, GardenEvent] = {}
    for card in soup.select(".events-list-item"):
        title_node = card.select_one(".event-title")
        link = card.select_one('a[href]')
        dates = [node for node in card.select(".events-list-info-start-end-time .date") if node.select_one(".date-month")]
        time_node = card.select_one(".event-time")
        if not title_node or not link or not dates or not time_node:
            continue
        try:
            start_date = _parse_date(dates[0])
            end_date = _parse_date(dates[-1]) if len(dates) > 1 else start_date
            time_text = " ".join(time_node.get_text(" ", strip=True).split())
            match = TIME_RANGE_RE.fullmatch(time_text)
            if not match:
                raise ValueError(f"Unrecognized time range: {time_text}")
            start_time, end_time = _parse_clock(match.group(1)), _parse_clock(match.group(2))
        except ValueError as exc:
            LOG.warning("Skipping event with invalid date/time: %s", exc)
            continue
        multi_day = start_date != end_date
        midnight_day = start_time == end_time == "00:00"
        event = GardenEvent(
            title=title_node.get_text(" ", strip=True), start_date=start_date, end_date=end_date,
            start_time=start_time, end_time=end_time, url=urljoin(CALENDAR_URL, link.get("href", "")),
            all_day=multi_day or midnight_day,
            daily_hours=time_text if multi_day and not midnight_day else None,
        )
        events[event.identity] = event
    if not events:
        raise ScrapeError("No events found; refusing to replace the known-good feed")
    return sorted(events.values(), key=lambda x: (x.start_date, x.start_time, x.title))


class GardenScraper:
    def __init__(self, session: requests.Session | None = None, timeout: int = 30):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.update({"User-Agent": "MoBotCalendar/0.1 (personal calendar feed; twice-daily fetch)"})

    def scrape(self) -> list[GardenEvent]:
        try:
            response = self.session.get(CALENDAR_URL, timeout=self.timeout)
            response.raise_for_status()
            events = parse_calendar(response.text)
            LOG.info("Parsed %d Garden event listings", len(events))
            return events
        except requests.RequestException as exc:
            raise ScrapeError(f"Garden calendar request failed: {exc}") from exc
