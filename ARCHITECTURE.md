# Architecture & Open-Source Foundation
**Project**: HypeNova AI / ViralForge AI  
**Author**: Principal AI Systems Architect

---

## 1. Open-Source Benchmark & Component Evaluation

Before architectural implementation, key open-source automated video clipping frameworks were analyzed:

| Framework | Core Capabilities | Licensing | Architectural Suitability |
| :--- | :--- | :--- | :--- |
| **ClipKaro** | Word-level Whisper timestamps, Hinglish speech model, YuNet facecam tracking, 9:16 smart reframe, audio loudness normalization, `post.json` export. | **MIT** | **Primary Base Foundation**. Selected for clean local-first execution, deep Hinglish support, and proven Windows compatibility. |
| **PostKaro** | Local OAuth publishing partner for YouTube Shorts, Instagram Reels, and Facebook. Secure keyring credential storage. | **MIT** | **Primary Publishing Partner**. Accepted format via `post.json`. |
| **OpenShorts** | Cloud/local shorts generator. | Multi-licensed (Cloud directory restricted) | Reused concepts for visual preset styling; avoided cloud-licensed components. |
| **ClippyMe / ClipMint** | Transcript-based highlight selection. | GPL / MIT | Examined for prompt design and scoring heuristics. |
| **ClipsAI** | Python library for sentence-based video trimming. | MIT | Ingested algorithm ideas for non-speech pause removal. |
| **FunClip** | Alibaba speech recognition & visual editor. | Apache 2.0 | Reference for ASR alignment. |

---

## 2. System Architecture Diagram

```mermaid
flowchart TD
    subgraph ScoutLayer["1. HypeScout (Autonomous Discovery)"]
        YT["YouTube Feeds / RSS"] --> SC["Scout Engine"]
        WL["Gaming & Podcast Watchlists"] --> SC
        UP["Creator Local Uploads"] --> SC
        SC --> DB_VID["Discovered Videos (SQLite WAL)"]
        SC --> RG["Strict Rights Verification Gate"]
    end

    subgraph IntelligenceLayer["2. HypeBrain (AI Viral Moment Engine)"]
        RG -->|"AUTHORIZED Media"| AS["Speech Recognition (faster-whisper CPU/GPU)"]
        AS --> WT["Word-Level Timestamps (words.json)"]
        WT --> GI["Gaming Event Intelligence (Irony, Crashes, Roasts)"]
        WT --> PI["Podcast Intelligence (Contrarian Hooks, Lessons)"]
        GI --> SE["7-Factor Viral Scoring (0-100)"]
        PI --> SE
        SE --> CR["Second-Pass Quality Critic"]
        CR --> CJ["clips.json"]
    end

    subgraph RenderLayer["3. HypeCut (Visual Editing Engine)"]
        CJ --> CUT["run.py cut (9:16 Vertical Reframing + Jump Cuts)"]
        CUT --> RF["Face Tracking (YuNet) & Adaptive Layouts"]
        RF --> ED["run.py edit (Zooms, Word-by-Word Captions, SFX)"]
        ED --> QA["run.py qa (Integrated Loudness -14 LUFS, Blank Frame Check)"]
        QA --> OUT["Final MP4 + SRT Subtitles"]
    end

    subgraph PackagingLayer["4. HypeRank (Packaging & SEO)"]
        OUT --> RK["Title Engine (5 Variants)"]
        RK --> HK["Hook Engine (3 Variants)"]
        RK --> SEO["Shorts Description & Platform Hashtags"]
        RK --> RISK["Advertiser Friendliness & Monetization Checks"]
    end

    subgraph DistributionLayer["5. Publishing & Business"]
        RISK --> PQ["Publishing Queue (Idempotent Guard)"]
        PQ --> PK["PostKaro Bridge / YouTube OAuth v3"]
        PQ --> CH_A["Profile A: ClutchRush Gaming"]
        PQ --> CH_B["Profile B: MicDrop Cuts"]
        PQ --> CL_SVC["Creator Client Clipping Packages (10/30/60)"]
    end

    subgraph DashboardLayer["6. HypeNova Studio (FastAPI + Modern UI)"]
        DB_VID <--> API["FastAPI REST Server (Port 8000)"]
        PQ <--> API
        OUT <--> API
        API <--> UI["Dark Mode Executive Dashboard (HTML5/CSS/JS)"]
    end
```

---

## 3. What Was Reused vs. Rewritten/Created New

### Reused from ClipKaro & PostKaro
* **Audio Extraction & ASR**: `clipper.fetch` using `faster-whisper` on INT8 quantized CPU execution.
* **Computer Vision Tracking**: OpenCV YuNet face detection for portrait framing and speaker centering.
* **Jump Cut Mechanics**: Automated speech activity detection to shorten dead pauses to a natural 0.2s without cutting spoken words.
* **Caption Rendering**: Dynamic ASS subtitle generation rendered via `libass` and `libx264`.
* **PostKit Schema**: `post.json` export specification ingested by PostKaro.

### Created New in HypeNova AI
* **Modular Python Package (`hypenova/`)**: Clean package architecture decoupled from interactive chat loops.
* **Persistent SQLite Database (`hypenova/database.py`)**: WAL mode database tracking watchlists, discovered videos, rights audit logs, jobs, clips, calendar queues, analytics, and business client packages.
* **Autonomous Content Scout (`hypenova/scout/`)**: YouTube RSS and API metadata discovery with rate-limiting, deduplication, and strict rights state machine.
* **7-Factor Viral Scoring Engine (`hypenova/brain/viral_engine.py`)**: Quantitative 0–100 heuristic score with second-pass critic review.
* **Gaming & Podcast Intelligence (`hypenova/brain/`)**: Rule engines detecting streamer boasts followed by unexpected failure, sarcastic comedy, in-game crashes, and contrarian interview hooks.
* **Visual Presets (`hypenova/editor/presets.py`)**: 6 ready-to-use production presets (`GTA Chaos`, `Indian Gaming Comedy`, `Clean Podcast`, `Cinematic Gaming`, `Quick News`, `Minimal Viral`).
* **Multi-Channel Distribution (`hypenova/publisher/channel_manager.py`)**: Distinct channel profiles (`ClutchRush Gaming`, `MicDrop Cuts`) with individual limits and publish modes.
* **Persistent Daily Automation Service (`hypenova/scheduler/automation_service.py`)**: Background service running durable cycles without requiring active AI chat sessions.
* **FastAPI Backend & Interactive Dark-Mode UI (`hypenova/api/` & `hypenova/ui/`)**: Full REST API and responsive desktop dashboard.
