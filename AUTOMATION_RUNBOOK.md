# Automation Runbook & Operations Guide
**Project**: HypeNova AI

---

## 1. Persistent Daily Workflow

The autonomous engine executes according to the following scheduled cadence:

```
Every 6 Hours   ──►  Discovery scan runs across curated gaming & podcast watchlists.
Every 2 Hours   ──►  Processing queue checks for new AUTHORIZED media files.
Continuous      ──►  Transcription (Whisper) -> Moment Detection -> Vertical Render -> QA.
Review Gate     ──►  Human review in HypeNova Dashboard (Default: Human Approval Required).
Scheduled Slot  ──►  PostKaro / YouTube OAuth uploads approved clips to target channels.
Every 24 Hours  ──►  Analytics refresh and performance index update.
```

---

## 2. Managing the Automation Service

### Running as a Foreground Process
```powershell
.\ClipKaro\.venv\Scripts\python.exe -m uvicorn hypenova.api.server:app --host 127.0.0.1 --port 8000
```

### Running as a Background Windows Service
To ensure HypeNova runs in the background on your Windows machine:
1. Run the server daemon via PowerShell:
   ```powershell
   Start-Process -FilePath ".\ClipKaro\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn hypenova.api.server:app --host 127.0.0.1 --port 8000" -WindowStyle Hidden
   ```
2. Or use the built-in Windows Task Scheduler script provided in `scripts/register_task.ps1` to automatically start HypeNova when your user logs in.

---

## 3. Laptop Sleep & System Constraints

> [!WARNING]
> Windows cannot execute tasks while a laptop is asleep, in hibernation, or powered off.
> - **State Preservation**: All queues, jobs, and discoveries are durably persisted in SQLite (`data/hypenova.db`). When the laptop wakes or restarts, the automation service automatically picks up exactly where it left off.
> - **Hosted Worker Migration (Optional Future Upgrade)**: For 24/7 continuous unattended processing without keeping your laptop on, the modular `hypenova/` backend can be deployed directly to a Linux VPS or cloud instance with Docker Compose.
