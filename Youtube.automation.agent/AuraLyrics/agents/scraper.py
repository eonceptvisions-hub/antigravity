"""
AuraLyrics — Scraper Agent (Agent A)
Scrapes Billboard Hot 100 chart and populates data/hits.json.
Supports auto mode (Billboard) and manual mode (CLI add).
Includes dedup logic to skip already-processed songs.
"""

import billboard
from datetime import datetime, timezone

from config import (
    BILLBOARD_CHART, DEFAULT_SONG_LIMIT, MAX_CHART_EXPANSION,
    STATUS_NEW, ensure_directories,
)
from utils.naming import generate_id
from utils.logger import log_event, get_console_logger
from utils.health import (
    load_hits, save_hits, find_song_by_id,
    should_process_song, print_health_report,
)

logger = get_console_logger("scraper")


class ScraperAgent:
    """Scrapes Billboard charts and manages the song queue."""

    def __init__(self):
        ensure_directories()

    def scrape_billboard(self, limit: int = DEFAULT_SONG_LIMIT) -> list:
        """
        Fetch current Billboard Hot 100 chart.
        Returns list of raw chart entries.
        """
        logger.info(f"Fetching Billboard {BILLBOARD_CHART} chart...")
        try:
            chart = billboard.ChartData(BILLBOARD_CHART)
            logger.info(f"Chart: {chart.title} | Date: {chart.date}")
            entries = []
            for song in chart[:limit]:
                entries.append({
                    "rank": song.rank,
                    "title": song.title,
                    "artist": song.artist,
                    "weeks_on_chart": song.weeks,
                    "peak_position": song.peakPos,
                })
            logger.info(f"Fetched {len(entries)} songs from chart")
            return entries
        except Exception as e:
            logger.error(f"Failed to fetch Billboard chart: {e}")
            log_event("scraper", "system", "scrape_chart", "failed", str(e))
            return []

    def add_song_to_queue(self, artist: str, title: str, rank: int = 99) -> bool:
        """
        Add a single song to the queue (manual mode).
        Returns True if added, False if duplicate.
        """
        song_id = generate_id(artist, title)

        if not should_process_song(song_id):
            logger.info(f"[{song_id}] '{artist} - {title}' already processed, skipping")
            return False

        hits = load_hits()
        existing = find_song_by_id(hits, song_id)

        if existing and existing.get("status") == STATUS_NEW:
            logger.info(f"[{song_id}] Already in queue as 'new', skipping")
            return False

        entry = {
            "rank": rank,
            "title": title.strip(),
            "artist": artist.strip(),
            "id": song_id,
            "status": STATUS_NEW,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "source": "manual",
        }

        if existing:
            # Update existing entry back to new
            for i, h in enumerate(hits):
                if h.get("id") == song_id:
                    hits[i] = {**existing, **entry}
                    break
        else:
            hits.append(entry)

        save_hits(hits)
        logger.info(f"[{song_id}] Added: '{artist} - {title}'")
        log_event("scraper", song_id, "add_song", "success",
                  extra={"artist": artist, "title": title})
        return True

    def run_auto(self, limit: int = DEFAULT_SONG_LIMIT) -> int:
        """
        Auto mode: scrape Billboard, dedup, add new songs.
        If all songs in top N are processed, expands search.
        Returns number of new songs added.
        """
        logger.info(f"Running AUTO mode (limit={limit})")
        added = 0
        current_limit = limit

        while added < limit and current_limit <= MAX_CHART_EXPANSION:
            chart_entries = self.scrape_billboard(current_limit)
            if not chart_entries:
                logger.error("No chart data available, aborting")
                break

            for entry in chart_entries:
                if added >= limit:
                    break

                song_id = generate_id(entry["artist"], entry["title"])

                if not should_process_song(song_id):
                    logger.info(
                        f"[{song_id}] '{entry['artist']} - {entry['title']}' "
                        f"already processed, skipping"
                    )
                    continue

                # Check if already in queue as 'new'
                hits = load_hits()
                existing = find_song_by_id(hits, song_id)
                if existing and existing.get("status") == STATUS_NEW:
                    logger.info(f"[{song_id}] Already queued, skipping")
                    continue

                # Add to queue
                new_entry = {
                    "rank": entry["rank"],
                    "title": entry["title"],
                    "artist": entry["artist"],
                    "id": song_id,
                    "status": STATUS_NEW,
                    "added_at": datetime.now(timezone.utc).isoformat(),
                    "weeks_on_chart": entry.get("weeks_on_chart"),
                    "peak_position": entry.get("peak_position"),
                    "source": "billboard",
                }

                hits = load_hits()  # Reload in case of concurrent writes
                if existing:
                    for i, h in enumerate(hits):
                        if h.get("id") == song_id:
                            hits[i] = new_entry
                            break
                else:
                    hits.append(new_entry)
                save_hits(hits)

                logger.info(
                    f"[{song_id}] #{entry['rank']} "
                    f"'{entry['artist']} - {entry['title']}' → queued"
                )
                log_event("scraper", song_id, "queue_song", "success",
                          extra={"rank": entry["rank"]})
                added += 1

            if added < limit:
                logger.info(
                    f"Only found {added}/{limit} new songs in top {current_limit}, "
                    f"expanding search..."
                )
                current_limit += 10

        logger.info(f"AUTO mode complete: {added} new songs added to queue")
        log_event("scraper", "system", "auto_run", "success",
                  extra={"songs_added": added})
        return added

    def run(self, mode: str = "auto", limit: int = DEFAULT_SONG_LIMIT,
            artist: str = None, title: str = None) -> int:
        """
        Main entry point for the scraper.
        
        Args:
            mode: 'auto' (Billboard) or 'manual' (single song)
            limit: Max songs to add (auto mode)
            artist: Artist name (manual mode)
            title: Song title (manual mode)
        
        Returns:
            Number of songs added
        """
        logger.info("=" * 50)
        logger.info("  Scraper Agent starting")
        logger.info("=" * 50)

        if mode == "manual":
            if not artist or not title:
                logger.error("Manual mode requires --artist and --title")
                return 0
            success = self.add_song_to_queue(artist, title)
            print_health_report()
            return 1 if success else 0
        else:
            count = self.run_auto(limit)
            print_health_report()
            return count
