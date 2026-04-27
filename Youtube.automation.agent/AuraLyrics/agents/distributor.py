"""
AuraLyrics — Distributor Agent (Agent E)
Uploads rendered lyric videos to YouTube using the official YouTube Data API v3.
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import (
    METADATA_DIR, RENDERS_DIR, STATUS_RENDERED, STATUS_UPLOADED
)
from utils.naming import build_filename
from utils.logger import get_console_logger, log_event
from utils.health import get_items_for_agent, update_song_status, report_failure

logger = get_console_logger("distributor")

# YouTube API scopes needed for uploading videos and setting thumbnails
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

class DistributorAgent:
    """Agent responsible for YouTube upload via official API."""

    def __init__(self):
        self.client_secrets_file = "client_secret.json"
        self.token_file = "token.json"
        self.youtube = None

    def _authenticate(self):
        """Handle OAuth 2.0 flow and build the YouTube service."""
        creds = None
        
        # Check if we already have a saved token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading saved token: {e}. Re-authenticating...")
                
        # If no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired Google token...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Refresh failed: {e}. Requesting new authorization...")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    logger.error("client_secret.json not found! Cannot authenticate with YouTube.")
                    return False
                
                logger.info("Starting Google OAuth flow...")
                try:
                    # This opens the browser for the user to grant permission
                    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Authentication flow failed: {e}")
                    return False
                    
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Failed to build YouTube service: {e}")
            return False

    def _upload_to_youtube(self, video_path: str, title: str, description: str, tags: list) -> bool:
        """Execute the upload using YouTube Data API."""
        if not self.youtube:
            return False
            
        try:
            logger.info("Preparing video for API upload...")
            
            body = {
                'snippet': {
                    'title': title[:100],
                    'description': description[:5000],
                    'tags': tags[:15],
                    'categoryId': '10' # 10 is Music
                },
                'status': {
                    'privacyStatus': 'public', # Options: public, private, unlisted
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Use resumable upload for larger files
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            logger.info("Uploading video chunks to YouTube...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    # We don't log every chunk to avoid spamming the console
                    if progress in [25, 50, 75]:
                        logger.info(f"Upload progress: {progress}%")
            
            video_id = response.get('id')
            logger.info(f"Upload complete! Video ID: {video_id}")
            return video_id
            
        except Exception as e:
            logger.error(f"API Upload failed: {str(e)}")
            return None

    def _set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Set a custom thumbnail for an uploaded video."""
        if not self.youtube or not thumbnail_path or not os.path.exists(thumbnail_path):
            return False
        try:
            media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logger.info(f"Thumbnail set for video {video_id}")
            return True
        except Exception as e:
            logger.warning(f"Thumbnail upload failed (video still uploaded): {e}")
            return False

    def run(self, limit: int = None) -> int:
        """Run the distributor agent to process 'rendered' songs."""
        logger.info("=" * 50)
        logger.info("  Distributor Agent starting (API Mode)")
        logger.info("=" * 50)

        songs = get_items_for_agent(STATUS_RENDERED)
        if not songs:
            logger.info("No 'rendered' songs to upload.")
            return 0

        if limit:
            songs = songs[:limit]
            
        logger.info(f"Found {len(songs)} videos to upload.")
        
        # Authenticate once for all videos
        if not self._authenticate():
            logger.error("Authentication failed. Aborting batch upload.")
            return 0
            
        # Initialize visual engine for thumbnail generation
        from agents.visual_engine import VisualEngineAgent
        thumb_engine = VisualEngineAgent()
        
        success_count = 0
        
        for song in songs:
            song_id = song["id"]
            artist = song["artist"]
            title = song["title"]
            rank = song["rank"]
            
            logger.info(f"[{song_id}] Preparing to upload: {artist} - {title}")
            
            video_path = os.path.join(RENDERS_DIR, build_filename(rank, artist, title, "mp4"))
            metadata_path = os.path.join(METADATA_DIR, build_filename(rank, artist, title, "json"))
            
            if not os.path.exists(video_path) or not os.path.exists(metadata_path):
                report_failure("distributor", song_id, "Missing video or metadata file")
                continue
                
            # Load metadata
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                
            yt_title = meta.get("title", f"{title} - {artist}")
            yt_desc = meta.get("description", "")
            yt_tags = meta.get("tags", [])
            
            # Generate thumbnail
            logger.info(f"[{song_id}] Generating thumbnail...")
            thumb_path = thumb_engine.generate_thumbnail(artist, title, rank)
            
            # Upload video
            video_id = self._upload_to_youtube(video_path, yt_title, yt_desc, yt_tags)
            
            if video_id:
                # Set custom thumbnail
                if thumb_path:
                    self._set_thumbnail(video_id, thumb_path)
                
                update_song_status(song_id, STATUS_UPLOADED)
                log_event("distributor", song_id, "upload", "success")
                success_count += 1
            else:
                report_failure("distributor", song_id, "API upload failed")
                
        logger.info(f"Distributor Agent complete: {success_count}/{len(songs)} uploaded successfully.")
        return success_count
