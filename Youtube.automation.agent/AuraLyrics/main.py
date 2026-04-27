"""
AuraLyrics — Master Orchestrator
Runs the full pipeline or individual agents.

Usage:
    python main.py                           # Full pipeline (auto mode)
    python main.py --agent scraper           # Run scraper only
    python main.py --agent scraper --limit 5 # Scrape top 5
    python main.py --add "Drake - Rich Baby" # Manually add a song
    python main.py --dry-run                 # Skip upload step
    python main.py --limit 3                 # Process top 3 songs
"""

import argparse
import sys
import os
import datetime

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_SONG_LIMIT, ensure_directories, STATUS_TRANSCRIBED
from utils.logger import get_console_logger
from utils.health import print_health_report, get_items_for_agent
from agents.scraper import ScraperAgent
from agents.asset_hunter import AssetHunterAgent
from agents.brain import BrainAgent
from agents.visual_engine import VisualEngineAgent
from agents.distributor import DistributorAgent

logger = get_console_logger("main")

BANNER = r"""
     _                    _               _          
    / \  _   _ _ __ __ _ | |   _   _ _ __(_) ___ ___ 
   / _ \| | | | '__/ _` || |  | | | | '__| |/ __/ __|
  / ___ \ |_| | | | (_| || |__| |_| | |  | | (__\__ \
 /_/   \_\__,_|_|  \__,_||_____\__, |_|  |_|\___|___/
                                |___/                 
  Autonomous Lyric Video Production Pipeline v1.0
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="AuraLyrics — Autonomous Lyric Video Pipeline",
    )
    parser.add_argument(
        "--agent",
        choices=["scraper", "asset_hunter", "brain", "visual_engine", "distributor"],
        help="Run a specific agent only",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "manual"],
        default="auto",
        help="Operating mode (default: auto)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_SONG_LIMIT,
        help=f"Max songs to process (default: {DEFAULT_SONG_LIMIT})",
    )
    parser.add_argument(
        "--add",
        type=str,
        help='Manually add a song: "Artist - Title"',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline but skip YouTube upload",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Print pipeline health report and exit",
    )
    parser.add_argument(
        "--cron",
        action="store_true",
        help="Enable daily execution safeguard (used for automated tasks)",
    )
    return parser.parse_args()


def run_scraper(args) -> int:
    """Run the scraper agent."""
    scraper = ScraperAgent()
    return scraper.run(
        mode=args.mode,
        limit=args.limit,
        artist=getattr(args, "_manual_artist", None),
        title=getattr(args, "_manual_title", None),
    )


def run_asset_hunter(args) -> int:
    """Run the asset hunter agent."""
    hunter = AssetHunterAgent()
    return hunter.run(limit=args.limit)


def run_brain(args) -> int:
    """Run the brain agent."""
    brain = BrainAgent()
    return brain.run(limit=args.limit)


def run_visual_engine(args) -> int:
    """Run the visual engine."""
    visual = VisualEngineAgent()
    return visual.run(limit=args.limit)


def run_distributor(args) -> int:
    """Run the distributor agent."""
    distributor = DistributorAgent()
    return distributor.run(limit=args.limit)


def run_pipeline(args):
    """Run the full pipeline sequentially with a dynamic retry loop."""
    logger.info("Starting full pipeline with dynamic retry loop...")
    target_count = args.limit
    
    while True:
        transcribed_songs = get_items_for_agent(STATUS_TRANSCRIBED)
        transcribed_count = len(transcribed_songs)
        
        if transcribed_count >= target_count:
            logger.info(f"Target of {target_count} transcribed songs reached. Proceeding to render.")
            break
            
        shortfall = target_count - transcribed_count
        logger.info(f"Currently have {transcribed_count} ready to render. Shortfall: {shortfall}. Fetching {shortfall} new songs...")
        
        args.limit = shortfall
        
        # Step 1: Scraper
        logger.info("─── Stage 1/5: Scraper Agent ───")
        added = run_scraper(args)
        if added == 0:
            logger.warning("No more songs available to scrape to meet the target. Breaking retry loop.")
            break

        # Step 2: Asset Hunter
        logger.info("─── Stage 2/5: Asset Hunter ───")
        run_asset_hunter(args)
        
        # Step 3: Brain Agent
        logger.info("─── Stage 3/5: Brain Agent ───")
        run_brain(args)
        
    # Reset limit to target_count for the final stages
    args.limit = target_count
        
    # Step 4: Visual Engine
    logger.info("─── Stage 4/5: Visual Engine ───")
    rendered = run_visual_engine(args)

    if not args.dry_run:
        # Step 5: Distributor
        logger.info("─── Stage 5/5: Distributor ───")
        uploaded = run_distributor(args)
    else:
        logger.info("─── Stage 5/5: Distributor ─── (skipped: --dry-run)")

    print_health_report()
    logger.info("Pipeline run complete!")


def main():
    print(BANNER)
    args = parse_args()
    ensure_directories()

    # Daily Execution Safeguard
    # Only enforce if the --cron flag is passed (e.g., from Task Scheduler)
    if args.cron:
        last_run_file = os.path.join("data", "last_run.txt")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(last_run_file):
            with open(last_run_file, "r") as f:
                if f.read().strip() == today:
                    logger.info("Pipeline already ran today. Safeguard activated. Exiting.")
                    sys.exit(0)
        with open(last_run_file, "w") as f:
            f.write(today)

    # Health report mode
    if args.health:
        print_health_report()
        return

    # Manual add mode
    if args.add:
        parts = args.add.split(" - ", 1)
        if len(parts) != 2:
            logger.error('Invalid format. Use: --add "Artist - Song Title"')
            sys.exit(1)
        args._manual_artist = parts[0].strip()
        args._manual_title = parts[1].strip()
        args.mode = "manual"

        scraper = ScraperAgent()
        scraper.run(
            mode="manual",
            artist=args._manual_artist,
            title=args._manual_title,
        )
        return

    # Single agent mode
    if args.agent:
        agent_map = {
            "scraper": run_scraper,
            "asset_hunter": run_asset_hunter,
            "brain": run_brain,
            "visual_engine": run_visual_engine,
            "distributor": run_distributor,
        }
        runner = agent_map.get(args.agent)
        if runner:
            runner(args)
        else:
            logger.error(f"Agent '{args.agent}' not yet implemented")
        return

    # Full pipeline mode
    run_pipeline(args)


if __name__ == "__main__":
    main()
