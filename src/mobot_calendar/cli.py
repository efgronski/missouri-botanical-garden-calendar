from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .archive import load_archive, reconcile, save_archive
from .calendar import save_calendar
from .scraper import GardenScraper, ScrapeError


def update(archive_path: Path, output_path: Path, scraper: GardenScraper | None = None) -> int:
    scraper = scraper or GardenScraper()
    try:
        current = scraper.scrape()
    except ScrapeError:
        logging.exception("Scrape failed; archive and calendar were left untouched")
        return 1
    combined = reconcile(load_archive(archive_path), current)
    save_archive(archive_path, combined)
    save_calendar(output_path, combined)
    for item in current[:8]:
        logging.info("%s to %s %s %s", item.start_date, item.end_date, item.start_time, item.title)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the Missouri Botanical Garden calendar feed")
    parser.add_argument("--archive", type=Path, default=Path("data/events.json"))
    parser.add_argument("--output", type=Path, default=Path("output/mobot.ics"))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(update(args.archive, args.output))


if __name__ == "__main__":
    main()
