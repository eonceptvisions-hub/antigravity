"""
AuraLyrics — Centralized Logger
Writes structured JSON logs to logs/system_health.json
and color-coded output to console.
"""

import json
import os
import logging
from datetime import datetime, timezone

from config import SYSTEM_HEALTH_LOG, LOGS_DIR


# ─── Console Logger Setup ────────────────────────────────────────────────────

class ColorFormatter(logging.Formatter):
    """Color-coded console output by severity."""

    COLORS = {
        logging.DEBUG:    "\033[90m",     # Grey
        logging.INFO:     "\033[36m",     # Cyan
        logging.WARNING:  "\033[33m",     # Yellow
        logging.ERROR:    "\033[31m",     # Red
        logging.CRITICAL: "\033[1;31m",   # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)


def get_console_logger(agent_name: str) -> logging.Logger:
    """Get a color-coded console logger for an agent."""
    logger = logging.getLogger(f"auralyrics.{agent_name}")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter(
            fmt=f"%(asctime)s │ {agent_name:>14s} │ %(levelname)-7s │ %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger


# ─── Structured JSON Logger ──────────────────────────────────────────────────

def log_event(
    agent: str,
    song_id: str,
    action: str,
    status: str,
    error_msg: str = None,
    extra: dict = None,
):
    """
    Append a structured JSON event to system_health.json.
    
    Args:
        agent: Agent name (e.g. 'scraper', 'asset_hunter')
        song_id: 4-char song ID or 'system' for non-song events
        action: What happened (e.g. 'scrape_chart', 'download_audio')
        status: Outcome (e.g. 'success', 'failed', 'skipped')
        error_msg: Error details if status is 'failed'
        extra: Additional data dict to include
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "song_id": song_id,
        "action": action,
        "status": status,
    }
    if error_msg:
        entry["error"] = error_msg
    if extra:
        entry.update(extra)

    # Append to JSON array file
    log_path = SYSTEM_HEALTH_LOG
    entries = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            entries = []

    entries.append(entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
