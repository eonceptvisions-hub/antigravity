"""
AuraLyrics — Self-Healing & Pipeline Health
Manages hits.json state, dedup checks, failure recovery.
"""

import json
import os
from datetime import datetime, timezone

from config import (
    HITS_JSON, DATA_DIR, UPLOAD_HISTORY_LOG, LOGS_DIR,
    STATUS_NEW, STATUS_UPLOADED, STATUS_FAILED, STATUS_UPLOAD_FAILED,
    STATUS_SKIPPED, MAX_RETRIES, PIPELINE_ORDER,
)
from utils.logger import log_event, get_console_logger

logger = get_console_logger("health")


def load_hits() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HITS_JSON):
        return []
    try:
        with open(HITS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning("hits.json corrupted, starting fresh")
        return []


def save_hits(hits: list):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HITS_JSON, "w", encoding="utf-8") as f:
        json.dump(hits, f, indent=2, ensure_ascii=False)


def find_song_by_id(hits: list, song_id: str):
    for entry in hits:
        if entry.get("id") == song_id:
            return entry
    return None


def update_song_status(song_id: str, new_status: str, extra_fields: dict = None):
    hits = load_hits()
    for entry in hits:
        if entry.get("id") == song_id:
            entry["status"] = new_status
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            if extra_fields:
                entry.update(extra_fields)
            break
    save_hits(hits)


def is_song_already_processed(song_id: str) -> bool:
    hits = load_hits()
    entry = find_song_by_id(hits, song_id)
    if entry is None:
        return False
    status = entry.get("status", "")
    if status in (STATUS_UPLOADED, STATUS_SKIPPED):
        return True
    if status in PIPELINE_ORDER and status != STATUS_NEW:
        return True
    return False


def is_song_in_upload_history(song_id: str) -> bool:
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(UPLOAD_HISTORY_LOG):
        return False
    try:
        with open(UPLOAD_HISTORY_LOG, "r", encoding="utf-8") as f:
            history = json.load(f)
        return any(h.get("song_id") == song_id for h in history)
    except (json.JSONDecodeError, IOError):
        return False


def should_process_song(song_id: str) -> bool:
    if is_song_already_processed(song_id):
        return False
    if is_song_in_upload_history(song_id):
        return False
    return True


def report_failure(agent: str, song_id: str, error: str):
    hits = load_hits()
    entry = find_song_by_id(hits, song_id)
    if entry:
        retries = entry.get("retry_count", 0) + 1
        entry["retry_count"] = retries
        entry["last_error"] = error
        entry["last_error_at"] = datetime.now(timezone.utc).isoformat()
        if retries >= MAX_RETRIES:
            entry["status"] = STATUS_FAILED
            logger.error(f"[{song_id}] Permanently failed after {retries} retries: {error}")
        else:
            logger.warning(f"[{song_id}] Failure #{retries}/{MAX_RETRIES}: {error}")
        save_hits(hits)
    log_event(agent, song_id, "failure", "failed", error_msg=error)


def get_items_for_agent(required_status: str) -> list:
    hits = load_hits()
    return [
        entry for entry in hits
        if entry.get("status") == required_status
        and entry.get("retry_count", 0) < MAX_RETRIES
    ]


def get_pipeline_health() -> dict:
    hits = load_hits()
    all_statuses = PIPELINE_ORDER + [STATUS_FAILED, STATUS_UPLOAD_FAILED, STATUS_SKIPPED]
    counts = {s: sum(1 for h in hits if h.get("status") == s) for s in all_statuses}
    return {
        "total": len(hits),
        "counts": counts,
        "pending_work": counts.get(STATUS_NEW, 0),
        "completed": counts.get(STATUS_UPLOADED, 0),
        "failed": counts.get(STATUS_FAILED, 0) + counts.get(STATUS_UPLOAD_FAILED, 0),
    }


def print_health_report():
    health = get_pipeline_health()
    logger.info("=" * 50)
    logger.info("    AuraLyrics Pipeline Health Report")
    logger.info("=" * 50)
    logger.info(f"  Total tracked:  {health['total']}")
    logger.info(f"  Pending (new):  {health['pending_work']}")
    logger.info(f"  Completed:      {health['completed']}")
    logger.info(f"  Failed:         {health['failed']}")
    logger.info("-" * 50)
    for status, count in health["counts"].items():
        if count > 0:
            logger.info(f"    {status:>15s}: {count}")
    logger.info("=" * 50)
