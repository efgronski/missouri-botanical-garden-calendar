from datetime import date
from pathlib import Path

from icalendar import Calendar

from mobot_calendar.archive import reconcile
from mobot_calendar.calendar import build_calendar
from mobot_calendar.cli import update
from mobot_calendar.models import GardenEvent
from mobot_calendar.scraper import ScrapeError, parse_calendar


def fixture(title="Japanese Festival", start=("September", "05", "2026"), end=None, hours="9:00 AM - 9:00 PM", url="/japanese-festival"):
    dates = f'<div class="date"><span class="date-month">{start[0]}</span><span class="date-day">{start[1]}</span><span class="date-year">{start[2]}</span></div>'
    if end:
        dates += f'<span class="sep">-</span><div class="date"><span class="date-month">{end[0]}</span><span class="date-day">{end[1]}</span><span class="date-year">{end[2]}</span></div>'
    return f'<div class="events-list-item"><h6 class="event-title">{title}</h6><div class="events-list-info-start-end-time">{dates}</div><span class="event-time">{hours}</span><a href="{url}">Learn More</a></div>'


def event(**kwargs):
    values = dict(title="Event", start_date="2026-09-05", end_date="2026-09-05", start_time="09:00", end_time="17:00", url="https://example.test/event")
    values.update(kwargs)
    return GardenEvent(**values)


def test_single_day_timed_event():
    page = fixture().replace('</div><span class="event-time">', '</div><div class="date"></div><span class="event-time">')
    item = parse_calendar(page)[0]
    assert (item.start_date, item.end_date, item.start_time, item.end_time, item.all_day) == ("2026-09-05", "2026-09-05", "09:00", "21:00", False)


def test_multiday_range_is_all_day_with_hours():
    item = parse_calendar(fixture(end=("September", "06", "2026")))[0]
    assert item.all_day and item.daily_hours == "9:00 AM - 9:00 PM"


def test_midnight_listing_is_all_day():
    assert parse_calendar(fixture(hours="12:00 AM - 12:00 AM"))[0].all_day


def test_same_title_different_times_are_distinct_and_uid_stable():
    a, b = event(), event(start_time="18:00", end_time="20:00")
    assert a.identity != b.identity and a.uid == event().uid


def test_dst_aware_timed_event_and_overnight_end():
    item = event(start_date="2026-11-01", end_date="2026-11-01", start_time="23:00", end_time="01:00")
    assert item.timed_start.utcoffset().total_seconds() == -21600
    assert item.timed_end.date().isoformat() == "2026-11-02"


def test_ics_all_day_end_is_exclusive():
    item = event(start_date="2026-09-05", end_date="2026-09-06", all_day=True, daily_hours="9:00 AM - 5:00 PM")
    component = next(x for x in Calendar.from_ical(build_calendar([item])).walk() if x.name == "VEVENT")
    assert component.decoded("dtend").isoformat() == "2026-09-07"


def test_archive_preserves_history_and_cancels_future_after_two_misses():
    past, future = event(start_date="2026-01-01", end_date="2026-01-01"), event(start_date="2026-12-01", end_date="2026-12-01")
    first = reconcile([past, future], [], today=date(2026, 9, 2))
    second = reconcile(first, [], today=date(2026, 9, 2))
    assert len(second) == 2 and next(x for x in second if x.start_date == "2026-12-01").status == "cancelled"


def test_failed_scrape_preserves_files(tmp_path: Path):
    archive, output = tmp_path / "events.json", tmp_path / "mobot.ics"
    archive.write_text("known-good"); output.write_text("known-good-calendar")
    class Broken:
        def scrape(self): raise ScrapeError("boom")
    assert update(archive, output, Broken()) == 1
    assert archive.read_text() == "known-good" and output.read_text() == "known-good-calendar"
