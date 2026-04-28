"""
AuraLyrics — Playwright Distributor Agent (Agent E - Stealth Mode)
Uploads rendered lyric videos to YouTube using Playwright and session cookies.
Optimized for GitHub Actions and Headless environments.
"""

import os
import json
import time
import random
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from config import (
    METADATA_DIR, RENDERS_DIR, STATUS_RENDERED, STATUS_UPLOADED,
    UPLOAD_MIN_DELAY, UPLOAD_MAX_DELAY, YOUTUBE_STUDIO_URL
)
from utils.naming import build_filename
from utils.logger import get_console_logger, log_event
from utils.health import get_items_for_agent, update_song_status, report_failure

logger = get_console_logger("distributor_playwright")

class PlaywrightDistributorAgent:
    """Agent responsible for YouTube upload via Playwright (Browser Automation)."""

    def __init__(self, headless=True):
        self.headless = headless
        self.cookie_file = "cookies.json"
        
    async def _human_delay(self):
        """Random delay to mimic human behavior."""
        await asyncio.sleep(random.uniform(UPLOAD_MIN_DELAY, UPLOAD_MAX_DELAY))

    async def _upload_video(self, browser_context, video_path, thumb_path, meta):
        """Orchestrates the browser steps to upload a single video."""
        page = await browser_context.new_page()
        await stealth_async(page)
        
        try:
            logger.info(f"Navigating to YouTube Studio: {YOUTUBE_STUDIO_URL}")
            await page.goto(YOUTUBE_STUDIO_URL)
            await self._human_delay()
            
            # Check if we are actually logged in
            if "login" in page.url:
                logger.error("Not logged in! Cookies might be expired or invalid.")
                return False

            # Click CREATE -> Upload videos
            # Note: YouTube Studio UI can be tricky, using robust selectors
            logger.info("Initiating upload flow...")
            await page.click("#create-icon")
            await self._human_delay()
            await page.click("#upload-icon")
            await self._human_delay()

            # Upload file
            logger.info(f"Selecting file: {os.path.basename(video_path)}")
            async with page.expect_file_chooser() as fc_info:
                await page.click("#select-files-button")
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path)
            
            # Wait for the upload dialog to transition to the metadata editor
            await page.wait_for_selector("#title-textarea", timeout=60000)
            logger.info("Metadata editor loaded.")

            # Set Title
            title = meta.get("title", "Lyric Video")[:100]
            logger.info(f"Setting title: {title}")
            await page.fill("#title-textarea #textbox", "") # Clear default
            await page.fill("#title-textarea #textbox", title)
            await self._human_delay()

            # Set Description
            desc = meta.get("description", "")[:5000]
            logger.info("Setting description...")
            await page.fill("#description-textarea #textbox", "")
            await page.fill("#description-textarea #textbox", desc)
            await self._human_delay()

            # Upload Thumbnail
            if thumb_path and os.path.exists(thumb_path):
                logger.info(f"Uploading thumbnail: {os.path.basename(thumb_path)}")
                async with page.expect_file_chooser() as fc_info:
                    await page.click("#file-loader") # This is usually the thumbnail upload button
                file_chooser = await fc_info.value
                await file_chooser.set_files(thumb_path)
                await self._human_delay()

            # Set "Not Made for Kids" (Mandatory)
            logger.info("Setting audience: Not for kids")
            await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MADE_FOR_KIDS"]')
            await self._human_delay()

            # Navigate through steps (Checks, etc.)
            # We click "NEXT" until we reach the Visibility tab
            for _ in range(3):
                logger.info("Clicking NEXT...")
                await page.click("#next-button")
                await self._human_delay()

            # Visibility Tab: Set to Public
            logger.info("Setting visibility to PUBLIC")
            await page.click('tp-yt-paper-radio-button[name="PUBLIC"]')
            await self._human_delay()

            # Final PUBLISH button
            logger.info("Clicking PUBLISH/DONE...")
            await page.click("#done-button")
            
            # Wait for success message or dialog to close
            await asyncio.sleep(10) 
            logger.info("Upload sequence completed.")
            return True

        except Exception as e:
            logger.error(f"Error during playwright upload: {str(e)}")
            # Take screenshot for debugging in CI
            if self.headless:
                await page.screenshot(path=f"logs/upload_error_{int(time.time())}.png")
            return False
        finally:
            await page.close()

    async def run_async(self, limit: int = None):
        """Main async entry point for the distributor."""
        songs = get_items_for_agent(STATUS_RENDERED)
        if not songs:
            logger.info("No 'rendered' songs to upload.")
            return 0

        if limit:
            songs = songs[:limit]

        logger.info(f"Found {len(songs)} videos to process via Playwright.")

        if not os.path.exists(self.cookie_file):
            logger.error(f"Cookie file {self.cookie_file} not found!")
            return 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            # Load cookies
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
            
            context = await browser.new_context()
            await context.add_cookies(cookies)
            
            # Initialize visual engine for thumbnail generation if needed
            from agents.visual_engine import VisualEngineAgent
            thumb_engine = VisualEngineAgent()
            
            success_count = 0
            for song in songs:
                song_id = song["id"]
                artist = song["artist"]
                title = song["title"]
                rank = song["rank"]
                
                logger.info(f"[{song_id}] Starting Playwright Upload: {artist} - {title}")
                
                video_path = os.path.join(RENDERS_DIR, build_filename(rank, artist, title, "mp4"))
                metadata_path = os.path.join(METADATA_DIR, build_filename(rank, artist, title, "json"))
                
                if not os.path.exists(video_path):
                    report_failure("distributor", song_id, "Video file missing")
                    continue
                
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                thumb_path = thumb_engine.generate_thumbnail(artist, title, rank)
                
                success = await self._upload_video(context, video_path, thumb_path, meta)
                
                if success:
                    update_song_status(song_id, STATUS_UPLOADED)
                    log_event("distributor", song_id, "upload", "success")
                    success_count += 1
                    # Small cooldown between videos
                    await asyncio.sleep(30)
                else:
                    report_failure("distributor", song_id, "Playwright upload failed")

            await browser.close()
            return success_count

    def run(self, limit: int = None):
        """Synchronous wrapper for main.py integration."""
        return asyncio.run(self.run_async(limit))

if __name__ == "__main__":
    # Test run
    agent = PlaywrightDistributorAgent(headless=False)
    agent.run(limit=1)
