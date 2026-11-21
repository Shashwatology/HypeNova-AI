"""HypeNova AI - Multi-Tenant Database Layer with SQLite WAL Mode & Workspace Isolation"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from hypenova.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Users Table (SaaS Identity)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,               -- Firebase UID or dev local UID
        email TEXT NOT NULL UNIQUE,
        display_name TEXT,
        photo_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Workspaces Table (Tenant Isolation)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        owner_user_id TEXT NOT NULL,
        tier TEXT DEFAULT 'CREATOR',       -- FREE, CREATOR, STUDIO
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_user_id) REFERENCES users (id)
    );
    """)

    # 3. Workspace Members (Role-Based Access Control)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workspace_members (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'OWNER', -- OWNER, ADMIN, EDITOR, VIEWER
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE (workspace_id, user_id)
    );
    """)

    # 4. Connected YouTube / Social Accounts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS connected_accounts (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        platform TEXT NOT NULL,            -- youtube, instagram, facebook
        account_email TEXT,
        channel_id TEXT NOT NULL,
        channel_title TEXT NOT NULL,
        channel_thumbnail TEXT,
        scopes_granted TEXT,               -- JSON list
        encrypted_token TEXT,              -- Server-side encrypted OAuth tokens
        status TEXT DEFAULT 'CONNECTED',   -- CONNECTED, EXPIRED, REVOKED
        last_synced_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 5. Sources Watchlist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        name TEXT NOT NULL,
        source_type TEXT NOT NULL,         -- youtube_channel, youtube_playlist, rss_feed, local_directory
        identifier TEXT NOT NULL,           -- URL or Channel ID
        category TEXT NOT NULL,             -- gaming, podcast, tech, news
        language TEXT DEFAULT 'hinglish',
        check_interval_hours INTEGER DEFAULT 6,
        last_checked_at TEXT,
        enabled INTEGER DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 6. Discovered Videos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS discovered_videos (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        source_id TEXT,
        external_id TEXT,
        title TEXT NOT NULL,
        channel_title TEXT,
        url TEXT NOT NULL,
        published_at TEXT,
        view_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        category TEXT,
        rights_status TEXT NOT NULL DEFAULT 'DISCOVERED',
        -- Statuses: DISCOVERED, SOURCE_REQUIRED, RIGHTS_REVIEW, AUTHORIZED, PROCESSING, READY_FOR_REVIEW, APPROVED, PUBLISHED, BLOCKED
        rights_notes TEXT,
        local_media_path TEXT,
        discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id),
        FOREIGN KEY (source_id) REFERENCES sources (id)
    );
    """)

    # 7. Processing Jobs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        job_type TEXT NOT NULL,             -- SCOUT, FETCH, TRANSCRIBE, CUT, EDIT, QA, PUBLISH
        target_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
        progress INTEGER DEFAULT 0,
        stage TEXT DEFAULT 'QUEUED',
        preset TEXT DEFAULT 'Indian Gaming Comedy',
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 8. Clips & Moments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clips (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        video_id TEXT NOT NULL,
        title TEXT NOT NULL,
        hook TEXT,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        duration REAL NOT NULL,
        viral_score REAL DEFAULT 0.0,
        score_breakdown TEXT,              -- JSON
        preset TEXT DEFAULT 'Indian Gaming Comedy',
        status TEXT DEFAULT 'CANDIDATE',   -- CANDIDATE, CUT, EDITED, APPROVED, SCHEDULED, PUBLISHED, REJECTED
        video_path TEXT,
        srt_path TEXT,
        post_metadata TEXT,                -- JSON
        qa_status TEXT DEFAULT 'PENDING',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id),
        FOREIGN KEY (video_id) REFERENCES discovered_videos (id)
    );
    """)

    # 9. Interactive Timeline Edits
    cur.execute("""
    CREATE TABLE IF NOT EXISTS timeline_edits (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        clip_id TEXT NOT NULL,
        trim_start REAL NOT NULL,
        trim_end REAL NOT NULL,
        captions_json TEXT NOT NULL,       -- JSON list of editable caption blocks
        preset TEXT DEFAULT 'Indian Gaming Comedy',
        safe_zones INTEGER DEFAULT 1,
        aspect_ratio TEXT DEFAULT '9:16',
        version INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id),
        FOREIGN KEY (clip_id) REFERENCES clips (id)
    );
    """)

    # 10. Channel Profiles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS channel_profiles (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        channel_handle TEXT,
        auth_status TEXT DEFAULT 'DISCONNECTED', -- DISCONNECTED, AUTHORIZED, EXPIRED
        publish_mode TEXT DEFAULT 'MANUAL',      -- MANUAL, AUTO_AUTHORIZED_ONLY
        daily_limit INTEGER DEFAULT 2,
        settings_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 11. Publishing Queue
    cur.execute("""
    CREATE TABLE IF NOT EXISTS publishing_queue (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        clip_id TEXT NOT NULL,
        channel_profile_id TEXT NOT NULL,
        scheduled_for TEXT NOT NULL,
        status TEXT DEFAULT 'QUEUED',       -- DRAFT, READY_FOR_REVIEW, APPROVED, QUEUED, UPLOADING, PUBLISHED, FAILED
        external_post_url TEXT,
        external_video_id TEXT,
        retry_count INTEGER DEFAULT 0,
        error_message TEXT,
        published_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id),
        FOREIGN KEY (clip_id) REFERENCES clips (id),
        FOREIGN KEY (channel_profile_id) REFERENCES channel_profiles (id)
    );
    """)

    # 12. Analytics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        clip_id TEXT,
        channel_profile_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        data_type TEXT DEFAULT 'OBSERVED',  -- OBSERVED (real API), BENCHMARK (experimental format)
        views INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        retention_rate REAL DEFAULT 0.0,
        hook_style TEXT,
        reporting_lag_hours INTEGER DEFAULT 48,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 13. Creator Services & Clients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        client_name TEXT NOT NULL,
        contact_email TEXT,
        package_tier TEXT DEFAULT '30_CLIPS', -- 10_CLIPS, 30_CLIPS, 60_CLIPS
        monthly_rate_inr INTEGER DEFAULT 25000,
        clips_delivered_this_month INTEGER DEFAULT 0,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 14. Cost Tracking
    cur.execute("""
    CREATE TABLE IF NOT EXISTS production_costs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL DEFAULT 'ws-default',
        clip_id TEXT,
        compute_seconds REAL DEFAULT 0.0,
        storage_mb REAL DEFAULT 0.0,
        api_tokens INTEGER DEFAULT 0,
        cost_inr REAL DEFAULT 0.0,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    );
    """)

    # 15. System Logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id TEXT DEFAULT 'ws-default',
        level TEXT DEFAULT 'INFO',
        module TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe multi-tenant column migrations for pre-existing databases
    tables_needing_workspace = [
        "discovered_videos", "jobs", "clips", "publishing_queue",
        "analytics", "clients", "production_costs", "sources",
        "channel_profiles", "system_logs"
    ]
    for tbl in tables_needing_workspace:
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN workspace_id TEXT DEFAULT 'ws-default';")
        except Exception:
            pass

    # Jobs stage and preset column migrations
    try:
        cur.execute("ALTER TABLE jobs ADD COLUMN stage TEXT DEFAULT 'QUEUED';")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE jobs ADD COLUMN preset TEXT DEFAULT 'Indian Gaming Comedy';")
    except Exception:
        pass

    # Publishing queue columns migration
    for col in ["external_video_id", "external_post_url", "published_at"]:
        try:
            cur.execute(f"ALTER TABLE publishing_queue ADD COLUMN {col} TEXT;")
        except Exception:
            pass

    # Analytics columns migration
    for col in ["platform", "data_type", "reporting_lag_hours"]:
        try:
            cur.execute(f"ALTER TABLE analytics ADD COLUMN {col} TEXT;")
        except Exception:
            pass

    # Ensure existing rows have workspace_id populated
    for tbl in tables_needing_workspace:
        try:
            cur.execute(f"UPDATE {tbl} SET workspace_id = 'ws-default' WHERE workspace_id IS NULL OR workspace_id = '';")
        except Exception:
            pass

    # Seed Default User & Workspace for local seamless transition
    cur.execute("""
    INSERT OR IGNORE INTO users (id, email, display_name)
    VALUES ('usr-admin', 'admin@hypenova.ai', 'Studio Lead');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspaces (id, name, slug, owner_user_id, tier)
    VALUES ('ws-default', 'HypeNova Primary Studio', 'primary-studio', 'usr-admin', 'STUDIO');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspace_members (id, workspace_id, user_id, role)
    VALUES ('mem-default', 'ws-default', 'usr-admin', 'OWNER');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspaces (id, name, slug, owner_user_id, tier)
    VALUES ('ws-clutchrush', 'ClutchRush Gaming', 'clutchrush-gaming', 'usr-admin', 'CREATOR');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspace_members (id, workspace_id, user_id, role)
    VALUES ('mem-clutchrush', 'ws-clutchrush', 'usr-admin', 'OWNER');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspaces (id, name, slug, owner_user_id, tier)
    VALUES ('ws-micdrop', 'MicDrop Cuts', 'micdrop-cuts', 'usr-admin', 'CREATOR');
    """)

    cur.execute("""
    INSERT OR IGNORE INTO workspace_members (id, workspace_id, user_id, role)
    VALUES ('mem-micdrop', 'ws-micdrop', 'usr-admin', 'OWNER');
    """)

    conn.commit()
    conn.close()

def log_event(module: str, message: str, level: str = "INFO", workspace_id: str = "ws-default"):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO system_logs (workspace_id, level, module, message) VALUES (?, ?, ?, ?);",
                     (workspace_id, level, module, message))
        conn.commit()
    except sqlite3.OperationalError:
        try:
            conn.execute("ALTER TABLE system_logs ADD COLUMN workspace_id TEXT DEFAULT 'ws-default';")
            conn.commit()
            conn.execute("INSERT INTO system_logs (workspace_id, level, module, message) VALUES (?, ?, ?, ?);",
                         (workspace_id, level, module, message))
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()
