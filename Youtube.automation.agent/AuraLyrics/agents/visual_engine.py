"""
AuraLyrics — Visual Engine (Agent D)
Renders lyric videos using CPU-friendly MoviePy and Pillow.
Optimized for low-memory, dynamic frame generation, and multiprocessing.
"""

import os
import re
import glob
import textwrap
import numpy as np
import random
import concurrent.futures
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, ImageClip, AudioFileClip, VideoClip

from config import (
    RAW_ASSETS_DIR, METADATA_DIR, RENDERS_DIR, BACKGROUNDS_DIR,
    STATUS_TRANSCRIBED, STATUS_RENDERED, STATUS_FAILED,
    VIDEO_RESOLUTION, VIDEO_FPS, VIDEO_BITRATE, FONT_PATH
)
from utils.naming import build_filename
from utils.logger import get_console_logger, log_event
from utils.health import get_items_for_agent, update_song_status, report_failure

logger = get_console_logger("visual_engine")


class VisualEngineAgent:
    """Agent responsible for rendering videos."""

    def __init__(self):
        os.makedirs(RENDERS_DIR, exist_ok=True)
        # Load all background files
        self.bgs = glob.glob(os.path.join(BACKGROUNDS_DIR, "*.*"))
            
    def time_to_seconds(self, time_str: str) -> float:
        """Convert HH:MM:SS,mmm to seconds."""
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def parse_srt(self, srt_path: str) -> list:
        """Parse SRT file into list of tuples: (start, end, text)."""
        subs = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                times = lines[1].split('-->')
                if len(times) == 2:
                    start = self.time_to_seconds(times[0].strip())
                    end = self.time_to_seconds(times[1].strip())
                    text = "\n".join(lines[2:]).strip()
                    subs.append((start, end, text))
                    
        # Make subtitles continuous (no gaps)
        # Extend the end time of each subtitle to the start time of the next
        for i in range(len(subs) - 1):
            subs[i] = (subs[i][0], subs[i+1][0], subs[i][2])
            
        return subs

    def generate_thumbnail(self, artist: str, title: str, rank: int) -> str:
        """Generate a clickable YouTube thumbnail (1280x720) with song title and artist."""
        THUMB_W, THUMB_H = 1280, 720
        output_path = os.path.join(RENDERS_DIR, build_filename(rank, artist, title, "jpg"))
        
        try:
            # Load a random background and resize to thumbnail dimensions
            bg_file = random.choice(self.bgs)
            bg = Image.open(bg_file).convert("RGB")
            
            # Crop/resize to fill 1280x720
            bg_ratio = bg.width / bg.height
            thumb_ratio = THUMB_W / THUMB_H
            if bg_ratio > thumb_ratio:
                new_h = THUMB_H
                new_w = int(bg.width * (THUMB_H / bg.height))
            else:
                new_w = THUMB_W
                new_h = int(bg.height * (THUMB_W / bg.width))
            bg = bg.resize((new_w, new_h), Image.LANCZOS)
            # Center crop
            left = (new_w - THUMB_W) // 2
            top = (new_h - THUMB_H) // 2
            bg = bg.crop((left, top, left + THUMB_W, top + THUMB_H))
            
            draw = ImageDraw.Draw(bg)
            
            # Cleaner Vertical Gradient Overlay (Darker at bottom for text contrast)
            overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            for y in range(THUMB_H):
                # Smooth transition to darkness at the bottom
                alpha = int(220 * (y / THUMB_H)) if y > THUMB_H * 0.3 else 0
                if alpha > 0:
                    overlay_draw.line([(0, y), (THUMB_W, y)], fill=(0, 0, 0, alpha))
            bg.paste(overlay, (0, 0), overlay)
            
            draw = ImageDraw.Draw(bg)
            
            # Load fonts
            try:
                font_title = ImageFont.truetype(FONT_PATH, 85)
                font_artist = ImageFont.truetype(FONT_PATH, 48)
                font_badge = ImageFont.truetype(FONT_PATH, 32)
            except:
                font_title = ImageFont.load_default()
                font_artist = font_title
                font_badge = font_title
            
            center_x = THUMB_W // 2
            
            # Wrap title
            wrapped_title = "\n".join(textwrap.wrap(title.upper(), width=22))
            
            # 1. Cleaner "LYRICS" Badge at the top
            badge_text = "🎵  L Y R I C S"
            # Subtle glow/shadow for badge
            draw.text((center_x + 1, 151), badge_text, font=font_badge, fill=(0, 0, 0, 100), anchor="mm")
            draw.text((center_x, 150), badge_text, font=font_badge, 
                      fill=(255, 215, 0, 255), anchor="mm") # Premium Gold
            
            # 2. Song Title (Clean white with soft shadow)
            # Offset shadow
            draw.text((center_x + 4, 354), wrapped_title, font=font_title,
                      fill=(0, 0, 0, 150), anchor="mm", align="center")
            draw.text((center_x, 350), wrapped_title, font=font_title,
                      fill=(255, 255, 255, 255), anchor="mm", align="center")
            
            # 3. Artist Name (Golden accent, clean)
            artist_text = artist.upper()
            draw.text((center_x + 2, 532), artist_text, font=font_artist,
                      fill=(0, 0, 0, 120), anchor="mm", align="center")
            draw.text((center_x, 530), artist_text, font=font_artist,
                      fill=(255, 215, 0, 230), anchor="mm", align="center")
            
            # Save as JPEG
            bg.save(output_path, "JPEG", quality=95)
            logger.info(f"Thumbnail generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    def render_video(self, song_id: str, artist: str, title: str, rank: int, audio_duration: float) -> bool:
        """Render the final video combining background, audio, and dynamic subtitle frames."""
        from bisect import bisect_right
        
        audio_path = os.path.join(RAW_ASSETS_DIR, build_filename(rank, artist, title, "mp3"))
        srt_path = os.path.join(METADATA_DIR, build_filename(rank, artist, title, "srt"))
        output_path = os.path.join(RENDERS_DIR, build_filename(rank, artist, title, "mp4"))
        
        if not os.path.exists(audio_path) or not os.path.exists(srt_path):
            report_failure("visual_engine", song_id, f"Missing audio or srt file for {artist}")
            return False
            
        if not self.bgs:
            report_failure("visual_engine", song_id, "No background file found in backgrounds/")
            return False
            
        try:
            logger.info(f"[{song_id}] Loading audio and subtitles...")
            audio_clip = AudioFileClip(audio_path)
            actual_duration = audio_clip.duration
            
            # Select random background
            bg_file = random.choice(self.bgs)
            ext = bg_file.lower().split('.')[-1]
            if ext in ['mp4', 'mov', 'avi']:
                bg_clip = VideoFileClip(bg_file).loop(duration=actual_duration)
            else:
                bg_clip = ImageClip(bg_file).with_duration(actual_duration)
                
            # Resize background to fill horizontal 16:9 dimensions
            target_w, target_h = VIDEO_RESOLUTION
            bg_clip = bg_clip.resized(width=target_w)
            if bg_clip.h > target_h:
                y_center = bg_clip.h / 2
                bg_clip = bg_clip.cropped(y1=y_center - target_h/2, 
                                          y2=y_center + target_h/2)
            else:
                bg_clip = bg_clip.resized(height=target_h)
            
            logger.info(f"[{song_id}] Pre-rendering text frames...")
            subs = self.parse_srt(srt_path)
            
            # Pre-load fonts
            try:
                font_active = ImageFont.truetype(FONT_PATH, 75)
            except Exception as e:
                logger.warning(f"[{song_id}] Could not load font, using default. Error: {e}")
                font_active = ImageFont.load_default()

            # === OPTIMIZATION 1: Pre-render ALL text frames upfront ===
            # Instead of rendering PIL images during encoding, do it all now.
            # For ~100 subtitle lines this uses ~400MB RAM but eliminates all
            # PIL work during the 5,400+ frame encoding loop.
            prerendered_rgb = []   # list of numpy arrays (H, W, 3)
            prerendered_alpha = [] # list of numpy arrays (H, W) float 0-1
            
            for i, (_, _, text) in enumerate(subs):
                img = Image.new('RGBA', VIDEO_RESOLUTION, (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                center_x = VIDEO_RESOLUTION[0] / 2
                center_y = VIDEO_RESOLUTION[1] / 2
                
                # Wrap text to cleanly fit 16:9 horizontally
                wrapped_text = "\n".join(textwrap.wrap(text, width=40))
                
                # Subtle drop shadow
                draw.text((center_x + 3, center_y + 3), wrapped_text, 
                          font=font_active, fill=(0, 0, 0, 150), align="center", anchor="mm")
                
                # Pure White Text
                draw.text((center_x, center_y), wrapped_text, font=font_active, 
                          fill=(255, 255, 255, 255), align="center", anchor="mm")

                arr = np.array(img)
                prerendered_rgb.append(arr[:, :, :3])
                prerendered_alpha.append(arr[:, :, 3].astype(np.float32) / 255.0)
            
            logger.info(f"[{song_id}] Pre-rendered {len(subs)} text frames. Starting encode...")

            # Empty frame for when no subtitle is active
            empty_rgb = np.zeros((VIDEO_RESOLUTION[1], VIDEO_RESOLUTION[0], 3), dtype=np.uint8)
            empty_alpha = np.zeros((VIDEO_RESOLUTION[1], VIDEO_RESOLUTION[0]), dtype=np.float32)
            
            # === OPTIMIZATION 2: Binary search for subtitle lookup ===
            # Build sorted start-time array for O(log n) lookup instead of O(n)
            sub_starts = [s[0] for s in subs]
            
            def get_sub_idx(t):
                idx = bisect_right(sub_starts, t) - 1
                if idx < 0:
                    return -1
                if t <= subs[idx][1]:  # check we're before end time
                    return idx
                return -1

            # === OPTIMIZATION 3: Single composite frame function ===
            # Instead of two separate VideoClips (rgb + mask), generate one
            # composited frame that blends text directly onto the background.
            # This halves the number of frame-function calls.
            
            # Get a static background frame (for image backgrounds)
            bg_frame = bg_clip.get_frame(0)
            is_static_bg = ext not in ['mp4', 'mov', 'avi']
            
            def make_frame(t):
                # Get background
                if is_static_bg:
                    frame = bg_frame.copy()
                else:
                    frame = bg_clip.get_frame(t).copy()
                
                idx = get_sub_idx(t)
                if idx == -1:
                    return frame
                
                start, end, _ = subs[idx]
                fade_duration = 0.3
                alpha_multiplier = 1.0
                
                # Fade in animation
                if t < start + fade_duration:
                    alpha_multiplier = (t - start) / fade_duration
                # Fade out animation
                elif t > end - fade_duration:
                    alpha_multiplier = (end - t) / fade_duration
                
                alpha_multiplier = max(0.0, min(1.0, alpha_multiplier))
                
                if alpha_multiplier < 0.01:
                    return frame
                
                # Alpha-blend pre-rendered text onto background
                alpha = prerendered_alpha[idx] * alpha_multiplier
                alpha_3d = alpha[:, :, np.newaxis]
                text_rgb = prerendered_rgb[idx]
                
                # Composite: result = text * alpha + bg * (1 - alpha)
                frame = (text_rgb * alpha_3d + frame * (1.0 - alpha_3d)).astype(np.uint8)
                return frame

            # Single VideoClip — no separate mask clip needed
            final_clip = VideoClip(frame_function=make_frame, duration=actual_duration)
            final_clip = final_clip.with_audio(audio_clip)
                
            logger.info(f"[{song_id}] Rendering MP4 ({actual_duration:.1f}s)...")
            final_clip.write_videofile(
                output_path,
                fps=VIDEO_FPS,
                codec="libx264",
                audio_codec="aac",
                bitrate=VIDEO_BITRATE,
                preset="ultrafast",
                threads=4, # FFMPEG encoding threads
                logger=None # Disable progress bar for clean logs in multiprocess
            )
            
            audio_clip.close()
            bg_clip.close()
            final_clip.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Render error for {song_id}: {str(e)}")
            report_failure("visual_engine", song_id, f"Rendering failed: {str(e)}")
            return False

    def run(self, limit: int = None) -> int:
        """Run the visual engine to process 'transcribed' songs in parallel."""
        logger.info("=" * 50)
        logger.info("  Visual Engine starting (Parallel CPU Mode)")
        logger.info("=" * 50)

        songs = get_items_for_agent(STATUS_TRANSCRIBED)
        if not songs:
            logger.info("No 'transcribed' songs to render.")
            return 0

        if limit:
            songs = songs[:limit]
            
        logger.info(f"Found {len(songs)} songs to render. Processing all {len(songs)} in parallel...")
        success_count = 0
        
        # Parallel Execution (7 workers to render all videos simultaneously)
        with concurrent.futures.ProcessPoolExecutor(max_workers=7) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self.render_video, 
                    song["id"], song["artist"], song["title"], song["rank"], song.get("duration_seconds", 0)
                ): song for song in songs
            }
            
            # Process as they complete
            for future in concurrent.futures.as_completed(futures):
                song = futures[future]
                try:
                    success = future.result()
                    if success:
                        # Safely update JSON tracking file in the main thread
                        update_song_status(song["id"], STATUS_RENDERED)
                        logger.info(f"[{song['id']}] Success: Video rendered!")
                        log_event("visual_engine", song["id"], "render", "success")
                        success_count += 1
                except Exception as exc:
                    logger.error(f"[{song['id']}] generated an exception: {exc}")
                
        logger.info(f"Visual Engine complete: {success_count}/{len(songs)} rendered successfully.")
        return success_count
