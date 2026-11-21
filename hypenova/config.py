"""HypeNova AI - Global Configuration & Environment Settings"""
import os
from pathlib import Path

# Workspace & Root Folders
BASE_DIR = Path(__file__).resolve().parent.parent
HYPENOVA_DIR = BASE_DIR / "hypenova"
CLIPKARO_DIR = BASE_DIR / "ClipKaro"
POSTKARO_DIR = BASE_DIR / "PostKaro"

# Python & Tool Binaries
PYTHON_VENV = CLIPKARO_DIR / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
FFMPEG_BIN = Path(r"C:\Users\shash\ffmpeg\bin\ffmpeg.exe") if os.name == "nt" else Path("ffmpeg")
FFPROBE_BIN = Path(r"C:\Users\shash\ffmpeg\bin\ffprobe.exe") if os.name == "nt" else Path("ffprobe")

# Storage & Data Paths
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = MEDIA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
RENDER_OUTPUT_DIR = CLIPKARO_DIR / "output"
DB_PATH = DATA_DIR / "hypenova.db"

# Server Settings
HOST = os.getenv("HYPENOVA_HOST", "127.0.0.1")
PORT = int(os.getenv("HYPENOVA_PORT", "8000"))

# Automation Timings (hours / minutes)
DEFAULT_DISCOVERY_INTERVAL_HOURS = 6
DEFAULT_QUEUE_UPDATE_INTERVAL_HOURS = 2
DEFAULT_ANALYTICS_INTERVAL_HOURS = 24

# Safety & Rights
DEFAULT_PUBLISH_MODE = "HUMAN_APPROVAL"  # HUMAN_APPROVAL or AUTO_AUTHORIZED_ONLY
ALLOW_AUTO_PUBLISH_EXTERNAL_CREATORS = False

# Content Channels
DEFAULT_CHANNELS = [
    {
        "id": "clutchrush-gaming",
        "name": "ClutchRush Gaming",
        "platform": "youtube",
        "niche": "gaming",
        "languages": ["hinglish", "english"],
        "description": "High-octane GTA gameplay, streamer comedy, and hilarious reaction clips.",
        "publish_mode": "MANUAL",
        "daily_limit": 2
    },
    {
        "id": "micdrop-cuts",
        "name": "MicDrop Cuts",
        "platform": "youtube",
        "niche": "podcast",
        "languages": ["hindi", "english"],
        "description": "Powerful podcast insights, unfiltered interviews, and thought-provoking life lessons.",
        "publish_mode": "MANUAL",
        "daily_limit": 1
    }
]
