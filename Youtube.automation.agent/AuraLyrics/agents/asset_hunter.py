"""
AuraLyrics — Asset Hunter Agent (Agent B)
Downloads official audio from YouTube for songs with status "new".
Uses yt-dlp to fetch the best audio and mutagen to extract duration.
"""

import os
import yt_dlp
from mutagen.mp3 import MP3

from config import (
    RAW_ASSETS_DIR, STATUS_NEW, STATUS_DOWNLOADED, 
    YTDLP_SEARCH_PREFIX, YTDLP_FORMAT, MIN_AUDIO_SIZE_BYTES
)
from utils.naming import build_filename
from utils.logger import get_console_logger, log_event
from utils.health import get_items_for_agent, update_song_status, report_failure

logger = get_console_logger("asset_hunter")


class AssetHunterAgent:
    """Agent responsible for downloading audio assets."""

    def __init__(self):
        os.makedirs(RAW_ASSETS_DIR, exist_ok=True)

    def download_audio(self, artist: str, title: str, output_path: str) -> bool:
        """
        Download audio using yt-dlp.
        Returns True if successful, False otherwise.
        """
        search_query = f"{YTDLP_SEARCH_PREFIX}{artist} {title} official audio"
        
        ydl_opts = {
            'format': YTDLP_FORMAT,
            'outtmpl': output_path.replace(".mp3", ""), # yt-dlp will add the extension during post-processing if needed
            'ffmpeg_location': os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(search_query, download=True)
            return True
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def get_audio_duration(self, filepath: str) -> float:
        """Extract audio duration in seconds using mutagen."""
        try:
            audio = MP3(filepath)
            return audio.info.length
        except Exception as e:
            logger.error(f"Failed to extract duration from {filepath}: {e}")
            return 0.0

    def run(self, limit: int = None) -> int:
        """
        Run the asset hunter to process 'new' songs.
        Args:
            limit: Maximum number of songs to download in this run.
        Returns:
            Number of songs successfully downloaded.
        """
        logger.info("=" * 50)
        logger.info("  Asset Hunter Agent starting")
        logger.info("=" * 50)

        songs = get_items_for_agent(STATUS_NEW)
        if not songs:
            logger.info("No 'new' songs to download.")
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
            
            logger.info(f"[{song_id}] Downloading: {artist} - {title}...")
            
            filename = build_filename(rank, artist, title, "mp3")
            output_path = os.path.join(RAW_ASSETS_DIR, filename)
            
            # Download
            success = self.download_audio(artist, title, output_path)
            
            if not success or not os.path.exists(output_path):
                error_msg = f"Download failed or output file not found: {output_path}"
                report_failure("asset_hunter", song_id, error_msg)
                continue
                
            # Verify file size
            file_size = os.path.getsize(output_path)
            if file_size < MIN_AUDIO_SIZE_BYTES:
                os.remove(output_path)
                error_msg = f"Downloaded file is too small ({file_size} bytes)."
                report_failure("asset_hunter", song_id, error_msg)
                continue
                
            # Get duration
            duration = self.get_audio_duration(output_path)
            if duration <= 0:
                os.remove(output_path)
                error_msg = "Failed to extract audio duration."
                report_failure("asset_hunter", song_id, error_msg)
                continue
                
            # Update status
            update_song_status(song_id, STATUS_DOWNLOADED, extra_fields={"duration_seconds": duration})
            
            logger.info(f"[{song_id}] Success: {duration:.1f}s | {file_size / 1024 / 1024:.2f} MB")
            log_event("asset_hunter", song_id, "download_audio", "success", extra={"duration_seconds": duration, "file_size_bytes": file_size})
            
            success_count += 1
            
        logger.info(f"Asset Hunter complete: {success_count}/{len(songs)} downloaded.")
        return success_count
