# HypeNova AI — Production Deployment & Infrastructure Specification

## 1. System Architecture Overview

HypeNova AI is designed to run seamlessly in both a **local single-machine environment** (such as our current Intel Core i5-12500T workstation) and a **cloud-native horizontally-scalable production cluster**.

```
                           +---------------------------+
                           |  Reverse Proxy & Ingress  |
                           |  (Nginx / Caddy / Traefik)|
                           +-------------+-------------+
                                         |
                         +---------------+---------------+
                         |                               |
                         v                               v
             +-----------------------+       +-----------------------+
             |   FastAPI Web API     |       |   FastAPI Web API     |
             |   (Uvicorn Worker 1)  |       |   (Uvicorn Worker 2)  |
             +-----------+-----------+       +-----------+-----------+
                         |                               |
                         +---------------+---------------+
                                         |
            +----------------------------+----------------------------+
            |                            |                            |
            v                            v                            v
  +--------------------+       +--------------------+       +--------------------+
  |    PostgreSQL 15   |       |    Redis Queue     |       | Cloudflare R2 / S3 |
  |   (Multi-Tenant)   |       |  (Job Distribution)|       |   (Media Storage)  |
  +--------------------+       +---------+----------+       +--------------------+
                                         |
                         +---------------+---------------+
                         |                               |
                         v                               v
             +-----------------------+       +-----------------------+
             |    GPU/CPU Worker 1   |       |    GPU/CPU Worker 2   |
             |  (Whisper ASR + FFmpeg|       |  (Whisper ASR + FFmpeg|
             +-----------------------+       +-----------------------+
```

---

## 2. Production Docker Compose Configuration

For containerized cloud deployment (AWS ECS, Google Cloud Run, DigitalOcean, or bare-metal Linux servers):

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: hypenova-postgres
    restart: always
    environment:
      POSTGRES_DB: hypenova
      POSTGRES_USER: hypenova_admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hypenova_admin -d hypenova"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: hypenova-redis
    restart: always
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: hypenova-api
    restart: always
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://hypenova_admin:${DB_PASSWORD}@db:5432/hypenova
      - REDIS_URL=redis://redis:6379/0
      - HYPENOVA_ENCRYPTION_KEY=${HYPENOVA_ENCRYPTION_KEY}
      - FIREBASE_SERVICE_ACCOUNT_KEY=/secrets/firebase-key.json
    volumes:
      - media_storage:/app/output
      - ./secrets:/secrets:ro
    ports:
      - "8000:8000"

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: hypenova-worker
    restart: always
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://hypenova_admin:${DB_PASSWORD}@db:5432/hypenova
      - REDIS_URL=redis://redis:6379/0
      - FFMPEG_BIN=/usr/bin/ffmpeg
    volumes:
      - media_storage:/app/output

volumes:
  pgdata:
  media_storage:
```

---

## 3. Local Windows Workstation Deployment (Dell PC)

When running as an automated background service on our local Intel Core i5-12500T Windows 11 workstation:

### A. Environment Optimization
- **Quantization**: Faster-Whisper uses `compute_type="int8"` for ultra-low memory CPU execution (~37s for 22s audio, consuming < 800 MB RAM).
- **Process Priority**: FFmpeg processes run with `BELOW_NORMAL_PRIORITY_CLASS` so normal desktop operations and video playback remain silky smooth without thermal throttling.
- **SQLite WAL Mode**: Provides concurrent reader threads without blocking writes.

### B. Windows Service / Autostart via PowerShell
To ensure HypeNova AI automatically recovers if the workstation reboots or updates:

```powershell
# Create an automated startup task running on user logon
$Action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\shash\Downloads\Youtube\scratch\start_server.ps1"'

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName 'HypeNovaServer' -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description 'HypeNova AI Background Engine Daemon'
```

---

## 4. Monitoring, Health Probes & Backup Strategy

1. **Liveness & Readiness Probes**:
   - `GET /api/health`: Returns HTTP 200 with disk space, CPU telemetry, and recent worker log output.
2. **Database Backup**:
   - For SQLite: Run `sqlite3 data/hypenova.db ".backup 'backups/hypenova-$(Get-Date -Format 'yyyyMMdd-HHmm').db'"` daily.
   - For PostgreSQL: Execute automated `pg_dump` snapshots to off-site object storage.
3. **Storage Retention**:
   - Automated cleanup job purges raw intermediate WAV files and temporary MP4 chunks older than 7 days, while retaining finalized vertical shorts (`output/*/edited/*.mp4`).
