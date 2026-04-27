"""
AuraLyrics — Standardized Naming Convention
Every file follows: {rank:02d}_{Artist}_{SongTitle}_{ID}.{ext}
Example: 01_Drake_RichBaby_a3f2.mp3
"""

import hashlib
import re


def sanitize(text: str) -> str:
    """
    Clean text for use in filenames.
    Removes special chars, replaces spaces with underscores,
    strips leading/trailing whitespace, collapses multiple underscores.
    """
    # Remove anything that isn't alphanumeric, space, or hyphen
    cleaned = re.sub(r"[^\w\s-]", "", text)
    # Replace spaces and hyphens with underscores
    cleaned = re.sub(r"[\s-]+", "_", cleaned)
    # Collapse multiple underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    # Strip leading/trailing underscores
    cleaned = cleaned.strip("_")
    return cleaned


def generate_id(artist: str, title: str) -> str:
    """
    Generate a deterministic 4-character hash ID from artist + title.
    This ensures the same song always gets the same ID regardless of rank.
    """
    raw = f"{artist.lower().strip()}::{title.lower().strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:4]


def build_filename(rank: int, artist: str, title: str, ext: str) -> str:
    """
    Build a standardized filename.
    
    Args:
        rank: Chart position (1-100)
        artist: Artist name
        title: Song title
        ext: File extension (without dot), e.g. 'mp3', 'srt', 'json'
    
    Returns:
        Formatted filename like '01_Drake_RichBaby_a3f2.mp3'
    """
    song_id = generate_id(artist, title)
    safe_artist = sanitize(artist)
    safe_title = sanitize(title)
    return f"{rank:02d}_{safe_artist}_{safe_title}_{song_id}.{ext}"


def parse_filename(filename: str) -> dict:
    """
    Parse a standardized filename back into components.
    
    Args:
        filename: e.g. '01_Drake_RichBaby_a3f2.mp3'
    
    Returns:
        Dict with keys: rank, artist, title, id, ext
        Returns None if filename doesn't match the expected pattern.
    """
    # Remove extension
    name, _, ext = filename.rpartition(".")
    if not name:
        return None

    # Pattern: {rank}_{rest}_{id}
    # The ID is always the last 4 chars before the extension
    parts = name.rsplit("_", 1)
    if len(parts) != 2 or len(parts[1]) != 4:
        return None

    song_id = parts[1]
    remaining = parts[0]

    # First part is the rank (2 digits)
    rank_match = re.match(r"^(\d{2})_(.+)$", remaining)
    if not rank_match:
        return None

    rank = int(rank_match.group(1))
    # Everything between rank and ID is artist_title (can't perfectly split)
    artist_title = rank_match.group(2)

    return {
        "rank": rank,
        "artist_title": artist_title,
        "id": song_id,
        "ext": ext,
        "original": filename,
    }


def build_song_id_from_entry(entry: dict) -> str:
    """Generate ID from a hits.json entry dict."""
    return generate_id(entry["artist"], entry["title"])
