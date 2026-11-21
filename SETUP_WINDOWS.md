# Windows Setup Guide — HypeNova AI
**Platform**: Windows 11 / Windows 10 (64-bit)

---

## 1. Prerequisites Installation

Run the following commands in an elevated or standard PowerShell terminal using `winget`:

```powershell
# 1. Install Python 3.12 (Do NOT use Python 3.15; onnxruntime requires <= 3.14)
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements

# 2. Install FFmpeg Full Build (with libx264 and libass for subtitle burning)
winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements

# 3. Install Node.js LTS (recommended for yt-dlp JavaScript challenge solver)
winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements

# 4. Install Git
winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
```

---

## 2. Environment Verification

Open a new PowerShell terminal and verify:

```powershell
# Verify Python 3.12
py -3.12 --version   # Output: Python 3.12.x

# Verify FFmpeg with required encoders and filters
ffmpeg -hide_banner -encoders | Select-String "libx264"
ffmpeg -hide_banner -filters  | Select-String "ass"

# Verify Node.js
node -v              # Output: v20+ or v24+
```

---

## 3. ClipKaro & HypeNova Environment Setup

```powershell
# Navigate to workspace
cd C:\Users\shash\Downloads\Youtube

# Ensure Python virtual environment is initialized
& "C:\Users\shash\AppData\Local\Programs\Python\Python312\python.exe" -m venv ClipKaro\.venv

# Install required dependencies
.\ClipKaro\.venv\Scripts\python.exe -m pip install -r ClipKaro\requirements.txt
.\ClipKaro\.venv\Scripts\python.exe -m pip install fastapi uvicorn starlette pydantic

# Seed the database and initial benchmark
.\ClipKaro\.venv\Scripts\python.exe -m hypenova.seed_data

# Run API and Pipeline tests
.\ClipKaro\.venv\Scripts\python.exe -m unittest hypenova/tests/test_api.py
.\ClipKaro\.venv\Scripts\python.exe ClipKaro\run.py test
```

---

## 4. Launching the HypeNova Dashboard

```powershell
.\ClipKaro\.venv\Scripts\python.exe -m uvicorn hypenova.api.server:app --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in any browser.
