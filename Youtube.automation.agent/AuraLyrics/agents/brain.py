"""
AuraLyrics — Brain Agent (Agent C)
Fetches synchronized lyrics from LRCLIB and generates YouTube metadata.
Enforces strict synchronization: skips songs without synced lyrics.
"""

import os
import json
import re
import datetime

from config import (
    METADATA_DIR, RAW_ASSETS_DIR, STATUS_DOWNLOADED, STATUS_TRANSCRIBED, STATUS_SKIPPED,
    LRCLIB_BASE_URL, LRCLIB_USER_AGENT
)
from utils.naming import build_filename
from utils.logger import get_console_logger, log_event
from utils.health import get_items_for_agent, update_song_status, report_failure

logger = get_console_logger("brain")


class BrainAgent:
    """Agent responsible for lyrics synchronization and metadata generation."""

    def __init__(self):
        os.makedirs(METADATA_DIR, exist_ok=True)
        self.headers = {
            "User-Agent": LRCLIB_USER_AGENT
        }

    def fetch_lyrics(self, artist: str, title: str, duration: float) -> str:
        """
        Query for synced lyrics using the syncedlyrics aggregator.
        Automatically searches across multiple providers (LRCLIB, Musixmatch, NetEase, etc).
        Returns the raw LRC string if found, otherwise None.
        """
        try:
            import syncedlyrics
            # Strip "(feat. XXX)" from title for better matching across all providers
            clean_title = re.sub(r'\(feat\..*?\)', '', title, flags=re.IGNORECASE).strip()
            query = f"{artist} {clean_title}"
            
            logger.info(f"[{title}] Searching multi-provider lyrics for: {query}")
            
            # search() returns the LRC string directly or None
            lrc_text = syncedlyrics.search(query)
            
            if lrc_text:
                logger.info(f"[{title}] Successfully found synced lyrics!")
                return lrc_text
            else:
                logger.warning(f"[{title}] No synced lyrics found across any provider.")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch lyrics using syncedlyrics: {e}")
            return None

    def convert_lrc_to_srt(self, lrc_text: str, duration: float) -> str:
        """
        Convert LRC formatted text to standard SRT subtitle format.
        Example LRC: [00:15.30] Text here
        Example SRT: 
        1
        00:00:15,300 --> 00:00:18,500
        Text here
        """
        lines = lrc_text.strip().split('\n')
        parsed_lines = []
        
        # Regex to match LRC timestamp [mm:ss.xx]
        regex = re.compile(r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)')
        
        for line in lines:
            match = regex.match(line.strip())
            if match:
                m = int(match.group(1))
                s = int(match.group(2))
                # LRC usually has hundredths, SRT needs thousandths
                ms_str = match.group(3)
                if len(ms_str) == 2:
                    ms = int(ms_str) * 10
                else:
                    ms = int(ms_str[:3])
                
                total_seconds = (m * 60) + s + (ms / 1000.0)
                text = match.group(4).strip()
                if text: # Ignore blank lines to keep video clean
                    parsed_lines.append((total_seconds, text))

        if not parsed_lines:
            return ""

        srt_content = ""
        for i in range(len(parsed_lines)):
            start_sec = parsed_lines[i][0]
            text = parsed_lines[i][1]
            
            # Determine end time
            if i < len(parsed_lines) - 1:
                end_sec = parsed_lines[i+1][0]
                # Cap duration of a single line to 5 seconds so it disappears if there's a long break
                if end_sec - start_sec > 5.0:
                    end_sec = start_sec + 5.0
            else:
                end_sec = min(start_sec + 5.0, duration)
            
            # Format to SRT timestamp (HH:MM:SS,mmm)
            def fmt_time(sec):
                td = datetime.timedelta(seconds=sec)
                hours, remainder = divmod(td.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                milliseconds = int(td.microseconds / 1000)
                return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
            
            srt_content += f"{i+1}\n"
            srt_content += f"{fmt_time(start_sec)} --> {fmt_time(end_sec)}\n"
            srt_content += f"{text}\n\n"
            
        return srt_content

    def generate_metadata(self, artist: str, title: str) -> dict:
        """Generate YouTube metadata (Title, Description, Tags)."""
        yt_title = f"{title} - {artist} | Lyrics 🎵"
        
        yt_desc = (
            f"Lyrics for '{title}' by {artist}\n\n"
            f"Listen to the official audio and support the artist!\n\n"
            f"Tags:\n"
            f"#{artist.replace(' ', '')} #{title.replace(' ', '')} #lyrics #music #trending"
        )
        
        tags = ["lyrics", artist, title, "trending", "music"]
        
        return {
            "title": yt_title,
            "description": yt_desc,
            "tags": tags,
            "visibility": "public"
        }

    def run(self, limit: int = None) -> int:
        """
        Run the brain agent to process 'downloaded' songs.
        """
        logger.info("=" * 50)
        logger.info("  Brain Agent starting (Strict LRC Mode)")
        logger.info("=" * 50)

        songs = get_items_for_agent(STATUS_DOWNLOADED)
        if not songs:
            logger.info("No 'downloaded' songs to transcribe.")
            return 0

        if limit:
            songs = songs[:limit]
            
        logger.info(f"Found {len(songs)} songs to process.")
        success_count = 0
        
        for song in songs:
            song_id = song["id"]
            artist = song["artist"]
            title = song["title"]
            rank = song["rank"]
            duration = song.get("duration_seconds", 0)
            
            logger.info(f"[{song_id}] Fetching lyrics for: {artist} - {title}")
            
            # 1. Fetch Lyrics
            lrc_text = self.fetch_lyrics(artist, title, duration)
            
            if not lrc_text:
                # STRICT POLICY: Abort and skip song
                logger.warning(f"[{song_id}] No synced lyrics found. Skipping song permanently.")
                update_song_status(song_id, STATUS_SKIPPED)
                log_event("brain", song_id, "transcribe", "skipped", error_msg="No synced LRC found")
                
                # Cleanup audio file to save space
                audio_path = os.path.join(RAW_ASSETS_DIR, build_filename(rank, artist, title, "mp3"))
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue
                
            # 2. Convert LRC to SRT
            srt_text = self.convert_lrc_to_srt(lrc_text, duration)
            if not srt_text:
                error_msg = "Failed to parse LRC timestamps into SRT."
                report_failure("brain", song_id, error_msg)
                continue
                
            # 3. Generate Metadata
            metadata = self.generate_metadata(artist, title)
            
            # 4. Save Files
            srt_filename = build_filename(rank, artist, title, "srt")
            srt_path = os.path.join(METADATA_DIR, srt_filename)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_text)
                
            json_filename = build_filename(rank, artist, title, "json")
            json_path = os.path.join(METADATA_DIR, json_filename)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
            # 5. Update Status
            update_song_status(song_id, STATUS_TRANSCRIBED)
            logger.info(f"[{song_id}] Success: generated {srt_filename} and metadata")
            log_event("brain", song_id, "transcribe", "success")
            
            success_count += 1
            
        logger.info(f"Brain Agent complete: {success_count}/{len(songs)} transcribed successfully.")
        return success_count
