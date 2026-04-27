# 🧠 AuraLyrics — Lyrics Synchronization Strategy

*This document explains the current logic for obtaining synchronized lyrics. It is kept here as a reference in case we decide to change or upgrade the strategy later.*

## Current Approach: Strict LRC (LRCLIB API)

Currently, the pipeline requires **perfect synchronization**. It does this by enforcing a strict requirement for timestamped LRC lyrics.

### The Flow
1. **Query:** The `BrainAgent` queries the free `lrclib.net` API using the `artist`, `title`, and the exact `duration` (in seconds) of the downloaded audio.
2. **Success:** If `syncedLyrics` are returned, it parses the LRC format (`[mm:ss.xx] line`) and converts it perfectly into a standard `.srt` subtitle file for the Visual Engine.
3. **Failure (The Strict Rule):** If the API only returns `plainLyrics` (no timestamps) or no match is found, the agent **aborts processing for that song**. The song's status is changed to `skipped`, its audio file is deleted to save space, and the pipeline simply moves on to the next trending song in the queue.

### Why this approach?
We are running on a CPU-only laptop, meaning we cannot use heavy AI models like Whisper to generate timestamps from raw audio. We also rejected the "even-split" mathematical estimation because songs have unpredictable instrumental breaks, leading to terrible sync quality. Skipping songs without synced lyrics guarantees 100% quality at the cost of volume.

## Future Upgrade Ideas (To Be Explored Later)

If skipping songs becomes an issue and we want higher coverage, we can explore these options later:
- **Aeneas (Force Alignment):** Use an open-source Python tool like Aeneas, which takes raw text lyrics and the audio file, and mathematically aligns them using a text-to-speech engine. It runs on CPU but requires complex installation (eSpeak + FFmpeg).
- **Secondary APIs:** Fallback to Megalobiz, RentAnAdviser, or scraping NetEase/QQ Music if LRCLIB fails.
- **Cloud APIs:** Use a generous free tier of an AI transcription service (e.g., Deepgram, AssemblyAI) to generate timestamps remotely. (Requires an API key).
