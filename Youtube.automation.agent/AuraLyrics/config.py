"""
AuraLyrics — Central Configuration
All paths, constants, and settings for the pipeline.
"""

import os

# ─── Project Root ────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ─── Directory Paths ─────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_ASSETS_DIR = os.path.join(PROJECT_ROOT, "raw_assets")
METADATA_DIR = os.path.join(PROJECT_ROOT, "metadata")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "renders")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
BACKGROUNDS_DIR = os.path.join(PROJECT_ROOT, "backgrounds")
FONTS_DIR = os.path.join(PROJECT_ROOT, "fonts")

# ─── Key File Paths ──────────────────────────────────────────────────────────
HITS_JSON = os.path.join(DATA_DIR, "hits.json")
SYSTEM_HEALTH_LOG = os.path.join(LOGS_DIR, "system_health.json")
UPLOAD_HISTORY_LOG = os.path.join(LOGS_DIR, "upload_history.json")

# ─── Scraper Settings ────────────────────────────────────────────────────────
BILLBOARD_CHART = "hot-100"
DEFAULT_SONG_LIMIT = 7
MAX_CHART_EXPANSION = 50  # If all top N are done, expand up to this

# ─── LRCLIB API ──────────────────────────────────────────────────────────────
LRCLIB_BASE_URL = "https://lrclib.net/api"
LRCLIB_USER_AGENT = "AuraLyrics/1.0 (https://github.com/auralyrics)"

# ─── Genius Fallback ─────────────────────────────────────────────────────────
GENIUS_SEARCH_URL = "https://genius.com/api/search/multi"
GENIUS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ─── yt-dlp Settings ─────────────────────────────────────────────────────────
YTDLP_FORMAT = "bestaudio/best"
YTDLP_SEARCH_PREFIX = "ytsearch1:"  # Search YouTube, take first result
MIN_AUDIO_SIZE_BYTES = 500 * 1024   # 500KB minimum to consider valid

# ─── Video Rendering ─────────────────────────────────────────────────────────
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
FONT_SIZE = 52
FONT_COLOR = (255, 255, 255)          # White
SHADOW_COLOR = (0, 0, 0, 204)         # Black at 80% opacity
SHADOW_OFFSET = 3
TEXT_Y_POSITION = 0.80                # 80% from top
TEXT_MAX_WIDTH_RATIO = 0.80           # 80% of frame width

# ─── YouTube Upload ──────────────────────────────────────────────────────────
UPLOAD_MIN_DELAY = 3   # seconds between browser actions
UPLOAD_MAX_DELAY = 7
YOUTUBE_STUDIO_URL = "https://studio.youtube.com"

# ─── Pipeline Status Values ──────────────────────────────────────────────────
# Visual Engine Settings
VIDEO_RESOLUTION = (1920, 1080)  # YouTube Horizontal 1080p
VIDEO_FPS = 30                   # 30fps is CPU friendly
VIDEO_BITRATE = "3000k"
FONT_PATH = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")

# Pipeline Status Constants
STATUS_NEW = "new"
STATUS_DOWNLOADED = "downloaded"
STATUS_TRANSCRIBED = "transcribed"
STATUS_RENDERED = "rendered"
STATUS_UPLOADED = "uploaded"
STATUS_FAILED = "failed"
STATUS_UPLOAD_FAILED = "upload_failed"
STATUS_SKIPPED = "skipped"

# All valid statuses in pipeline order
PIPELINE_ORDER = [
    STATUS_NEW,
    STATUS_DOWNLOADED,
    STATUS_TRANSCRIBED,
    STATUS_RENDERED,
    STATUS_UPLOADED,
]

# ─── Self-Healing ────────────────────────────────────────────────────────────
MAX_RETRIES = 3


def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_DIR, RAW_ASSETS_DIR, METADATA_DIR,
        RENDERS_DIR, LOGS_DIR, BACKGROUNDS_DIR, FONTS_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
