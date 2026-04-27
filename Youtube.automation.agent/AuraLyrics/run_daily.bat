@echo off
echo Starting AuraLyrics Daily Run...
cd /d "C:\Users\arinc\OneDrive\Documents\antigravity\Youtube.automation.agent\AuraLyrics"

:: Activate virtual environment and run the pipeline
call .\venv\Scripts\activate.bat
python main.py --cron >> logs\daily_cron.log 2>&1

echo Run complete.
