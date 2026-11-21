# HypeNova AI ⚡
### Autonomous Short-Form Content Production & Publishing Platform
*From Moments to Momentum.*

---

## 1. Overview

**HypeNova AI** (incorporating the ViralForge AI intelligence suite) is a production-oriented, local-first content studio designed to autonomously discover, analyze, cut, visually style, package, and publish high-retention vertical short-form videos (9:16) for **YouTube Shorts**, **Instagram Reels**, and **TikTok**.

The platform is built on top of:
- **ClipKaro Engine**: Local Whisper speech recognition, audio cue detection, YuNet face tracking, dynamic zooms, word-by-word animated subtitles, audio normalization (-14 LUFS), and QA validation.
- **PostKaro Partner System**: Local encrypted OAuth publishing workflows for YouTube, Instagram, and Facebook.
- **HypeNova Core Layer**: Autonomous scout (HypeScout), 7-factor viral moment engine (HypeBrain), premium visual preset renderer (HypeCut), packaging & SEO engine (HypeRank), multi-channel profiles (ClutchRush Gaming & MicDrop Cuts), persistent SQLite automation scheduler, and an executive dark-mode browser dashboard.

---

## 2. Key Modules & Operational Features

| Module | Purpose | Status |
| :--- | :--- | :--- |
| **HypeScout** | RSS & API-based discovery across curated Indian/international gaming & podcast watchlists with strict rights classification. | **Fully Functional** |
| **HypeBrain** | Multimodal moment engine with gaming-specific irony detection (boast-to-failure), roast/laughter recognition, podcast contrarian hooks, and 7-factor viral potential scoring (0–100). | **Fully Functional** |
| **HypeCut** | 1080×1920 vertical export with visual presets (`GTA Chaos`, `Indian Gaming Comedy`, `Clean Podcast`, `Cinematic Gaming`, `Quick News`, `Minimal Viral`), safe caption zones, and profanity handling. | **Fully Functional** |
| **HypeRank** | Generates 5 title options, 3 opening hooks, SEO descriptions, hashtags, Instagram captions, and monetization warnings. | **Fully Functional** |
| **HypeNova Studio UI** | Executive dark-mode dashboard running on FastAPI + modern HTML5/CSS3 at `http://127.0.0.1:8000`. | **Live & Operational** |
| **Publishing Bridge** | Generates validated `post.json` packages compatible with PostKaro and direct official OAuth endpoints. | **Fully Functional** |
| **Daily Automation** | Durable background scheduler with configurable scan intervals (6h discovery, 2h queue, daily analytics). | **Fully Functional** |

---

## 3. Quick Start & Startup Commands

### Start the HypeNova Dashboard & Server
From the project root:
```powershell
# Activate environment and launch the FastAPI server
.\ClipKaro\.venv\Scripts\python.exe -m uvicorn hypenova.api.server:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

### Run API & Unit Tests
```powershell
# Run ClipKaro engine self-tests (80 tests)
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py test

# Run HypeNova API integration tests (6 tests)
.\ClipKaro\.venv\Scripts\python.exe -m unittest hypenova/tests/test_api.py
```

### Run an End-to-End Clipping Workflow
```powershell
# 1. Fetch, extract audio, and transcribe with Whisper
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py fetch "C:\path\to\your\video.mp4" --model base --device cpu --lang en

# 2. Cut to 9:16 vertical video
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py cut <project-slug>

# 3. Apply visual styling, zooms, and word-by-word captions
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py edit <project-slug>

# 4. Run automated QA checks
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py qa <project-slug>

# 5. Export PostKaro distribution payload
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py post <project-slug>
```

---

## 4. Hardware Requirements & CPU/GPU Execution

* **CPU Mode (Tested & Active)**: 12th Gen Intel Core i5-12500T (16 GB RAM). Transcribes in INT8 mode via CTranslate2. Renders via multi-threaded libx264.
* **Optional GPU Acceleration**: With an NVIDIA GPU (RTX 4050 or higher, 4 GB+ VRAM), transcription speed increases by ~5–10x. The system automatically detects an NVIDIA GPU when available and falls back safely to CPU execution without breaking changes.
* **Storage**: Local filesystem storage with SQLite WAL mode. Temporary render artifacts are cleaned up after QA verification.

---

## 5. Strict Rights & Monetization Safeguards

> [!IMPORTANT]
> A discovered YouTube URL is a public reference, **not** authorization to download or republish third-party content.
> HypeNova AI enforces strict rights verification:
> - Content is tagged `DISCOVERED` or `SOURCE_REQUIRED` until rights evidence is provided.
> - Only videos marked `AUTHORIZED` (e.g. creator-owned files, authorized client submissions) enter the processing pipeline.
> - The default operational mode is **Automated Production + Human Approval for Publishing**.
