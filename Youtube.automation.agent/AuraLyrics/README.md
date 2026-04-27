# 🛸 AuraLyrics

Autonomous Lyric Video Production Pipeline — zero-cost, fully automated.

---

## ⚡ Quick Start

```powershell
# 1. Navigate to project
Set-Location c:\Users\arinc\OneDrive\Documents\antigravity\Youtube.automation.agent\AuraLyrics

# 2. First-time setup (creates venv, installs deps, creates folders)
powershell -ExecutionPolicy Bypass -File setup.ps1

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Run the scraper
python main.py --agent scraper --limit 5
```

---

## 📋 All Commands

### Pipeline Commands

| Command | What it does |
|---------|-------------|
| `python main.py` | Run full pipeline (scrape → download → lyrics → render → upload) |
| `python main.py --health` | Check current pipeline progress and song statuses |
| `python main.py --dry-run` | Run full pipeline but skip YouTube upload |
| `python main.py --limit 5` | Process only 5 songs |

### Run Individual Agents

| Command | What it does |
|---------|-------------|
| `python main.py --agent scraper` | Scrape Billboard Hot 100 only |
| `python main.py --agent scraper --limit 5` | Scrape top 5 trending songs |
| `python main.py --agent asset_hunter` | Download audio for queued songs *(coming soon)* |
| `python main.py --agent brain` | Fetch lyrics + generate metadata *(coming soon)* |
| `python main.py --agent visual_engine` | Render lyric videos *(coming soon)* |
| `python main.py --agent distributor` | Upload to YouTube *(coming soon)* |

### Manually Add Songs

```powershell
# Add a specific song
python main.py --add "Drake - Rich Baby"
python main.py --add "Kendrick Lamar - Not Like Us"
python main.py --add "Taylor Swift - Anti-Hero"
```

> Format is always `"Artist - Song Title"` (separated by ` - `)

### Health & Status

```powershell
# See how many songs are at each stage
python main.py --health
```

---

## 📁 Project Structure

```
AuraLyrics/
├── main.py              # Master orchestrator (run this)
├── config.py            # All settings and paths
├── requirements.txt     # Python dependencies
├── setup.ps1            # First-time setup script
│
├── agents/              # The 5 pipeline agents
│   ├── scraper.py       # Billboard chart scraper
│   ├── asset_hunter.py  # Audio downloader (coming soon)
│   ├── brain.py         # Lyrics fetcher (coming soon)
│   ├── visual_engine.py # Video renderer (coming soon)
│   └── distributor.py   # YouTube uploader (coming soon)
│
├── utils/               # Shared utilities
│   ├── naming.py        # File naming conventions
│   ├── logger.py        # Logging system
│   └── health.py        # Self-healing + dedup
│
├── data/
│   └── hits.json        # 📊 MASTER LIST — all tracked songs
│
├── raw_assets/          # Downloaded .mp3 audio files
├── metadata/            # .srt subtitles + .json descriptions
├── renders/             # Final .mp4 lyric videos
├── backgrounds/         # YOUR video/image templates (add here!)
├── fonts/               # Fonts for subtitle rendering
│
└── logs/
    ├── system_health.json    # Error and activity log
    └── upload_history.json   # Past YouTube uploads
```

---

## 🔄 Song Status Flow

Each song in `data/hits.json` moves through these statuses:

```
new → downloaded → transcribed → rendered → uploaded
                                              ✅ Done!

If anything fails:
new → failed (after 3 retries, song is skipped)
```

| Status | Meaning |
|--------|---------|
| `new` | Queued, waiting for audio download |
| `downloaded` | Audio saved, waiting for lyrics |
| `transcribed` | Lyrics + metadata ready, waiting for render |
| `rendered` | Video ready in `renders/`, waiting for upload |
| `uploaded` | Published to YouTube ✅ |
| `failed` | Failed 3 times, permanently skipped |

---

## 🧠 How Dedup Works

- Running the scraper twice **will NOT create duplicates**
- Songs already in the queue are skipped automatically
- If all top N songs are already queued, the scraper **auto-expands** down the chart to find fresh songs
- Previously uploaded songs are never re-processed

---

## ⚠️ Prerequisites

- **Python 3.10+** — installed
- **ffmpeg** — needed for audio/video processing (install with `winget install Gyan.FFmpeg`)
- **No GPU required** — entire pipeline runs on CPU
- **No API keys** — everything uses free, open sources
