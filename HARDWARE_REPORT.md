# Hardware & Environment Compatibility Report
**Project**: HypeNova AI / ViralForge AI  
**Generated On**: November 2026  
**Host Machine Architecture**: Dell Micro / Desktop Platform

---

## 1. Machine Hardware Profile

| Component | Specification | Operational Status |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Pro 64-bit (Build 26200) | Fully Compatible |
| **Processor (CPU)** | 12th Gen Intel(R) Core(TM) i5-12500T (6 Cores, 12 Logical Processors, 2.0 GHz) | Active, CPU Transcoding & Whisper |
| **System RAM** | 16 GB Total Visible (16,456 MB), ~8.5 GB Available | Ample for 1080p rendering and Whisper base/large |
| **Storage (Disk)** | Drive `C:\`: 475 GB Total, **239.7 GB Free** | Ample for project cache and source video assets |
| **Display / GPU** | Intel(R) UHD Graphics 770 (Driver 32.0.101.7085, 2 GB AdapterRAM) | Active Display Controller |
| **NVIDIA GPU Status** | Discrete NVIDIA GPU not detected on this physical chassis (`nvidia-smi` absent) | **Operating with CPU Fallback Mode** |

---

## 2. Installed Software & Toolchains

| Tool | Detected Version | Purpose |
| :--- | :--- | :--- |
| **Python** | Python 3.12.10 (`C:\Users\shash\AppData\Local\Programs\Python\Python312\python.exe`) | Core backend, AI clipping pipeline, FastAPI |
| **FFmpeg** | FFmpeg 9.1-full_build (Gyan.dev, gcc 16.2.0) | Video cutting, 9:16 vertical cropping, libx264, libass subtitle burning |
| **FFprobe** | FFprobe 9.1-full_build | Media stream probing, duration, loudness calculation |
| **Node.js** | Node.js v24.12.0 (`C:\Program Files\nodejs\node.exe`) | yt-dlp JS challenge solver & optional Remotion engine |
| **Git** | Git 2.51.0 (`C:\Program Files\Git\cmd\git.exe`) | Version control and repo management |
| **PostgreSQL** | PostgreSQL 18 Client (`C:\Program Files\PostgreSQL\18`) | Optional production enterprise storage |

---

## 3. ClipKaro Environment Compatibility

* **Virtual Environment**: Initialized at `c:\Users\shash\Downloads\Youtube\ClipKaro\.venv`.
* **Core Libraries Installed**:
  - `faster-whisper`: 1.2.1 (OpenAI Whisper models via CTranslate2 on CPU)
  - `ctranslate2`: 4.9.0
  - `onnxruntime`: 1.32.0 (Silero VAD, YAMNet laughter, SwiftF0 pitch)
  - `opencv-python`: 5.1.0.95 (Face tracking YuNet, frame reframing, zooms)
  - `yt-dlp`: 2026.10.26 (Media extraction)
  - `soundfile`: 0.14.0
  - `swift-f0`: 0.3.0
* **Unit Tests Status**: **80/80 tests passed** in 4.28s.
* **Thermal & Resource Guidelines**:
  - CPU whisper transcription runs with INT8 quantization (`compute_type='int8'`).
  - Video rendering uses multi-threaded `libx264` with phone-optimized loudness normalisation (-14 LUFS).
  - CPU usage stays strictly bounded, preventing thermal throttling or system lockup.
