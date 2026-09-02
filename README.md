# Missouri Botanical Garden Calendar

An unofficial, self-updating iCalendar feed for events listed on the [Missouri Botanical Garden calendar](https://www.missouribotanicalgarden.org/events-classes/calendar).

This personal project is not affiliated with the Missouri Botanical Garden.

## Calendar behavior

- Single-day events are normal timed events in `America/Chicago`.
- Midnight-to-midnight listings are all-day events.
- Multi-day exhibitions and date ranges are represented by one all-day banner spanning the range, with the advertised daily hours in the description. This avoids filling every day with duplicate events for year-long exhibitions.
- Titles begin with 🌿 and link to the Garden's detail page.
- Events use deterministic IDs derived from the detail URL, title, dates, and times.

The source page is server-rendered and already contains current and upcoming events far into the future, so each update requires only one HTTP request.

## Run locally

Python 3.11 or newer is required.

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
python -m mobot_calendar
```

The generated feed is `output/mobot.ics`.

## Archive and cancellations

`data/events.json` preserves historical listings. A future listing absent from two consecutive successful scrapes is marked cancelled. Failed or empty scrapes never overwrite the archive or known-good feed. A changed date or time produces a new stable identity; the prior future event is conservatively cancelled after two misses.

## GitHub automation and publishing

The update workflow runs approximately twice daily and can also be started from **Actions → Update calendar → Run workflow**. It tests the project, regenerates the archive/feed, and commits only actual changes.

To publish:

1. Create a public repository named `missouri-botanical-garden-calendar` and push this project to `main`.
2. Select **Settings → Pages → Source: GitHub Actions**.
3. Select **Settings → Actions → General → Workflow permissions → Read and write permissions**.
4. Run **Actions → Publish calendar** once.

The subscription URL will be:

```text
https://YOUR-USERNAME.github.io/missouri-botanical-garden-calendar/mobot.ics
```

Subscribe using “From URL” or “New Calendar Subscription,” not a one-time file import. Calendar clients control their own refresh interval, so changes may take several hours to appear.
