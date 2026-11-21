"""HypeNova AI - Database Initializer & Real Test Data Seeder"""
import json
from hypenova.database import get_connection, init_db, log_event
from hypenova.scout.scout_engine import HypeScout
from hypenova.publisher.channel_manager import ChannelManager

def seed():
    init_db()
    scout = HypeScout()
    scout.seed_default_sources()
    
    ch_mgr = ChannelManager()
    ch_mgr.init_channels()

    conn = get_connection()
    cur = conn.cursor()

    # Ensure local upload source exists for FK
    cur.execute("""
    INSERT OR IGNORE INTO sources (id, workspace_id, name, source_type, identifier, category, notes)
    VALUES ('local-upload', 'ws-default', 'Creator Local Uploads', 'local_directory', 'media/uploads', 'gaming', 'Direct creator-provided media files.');
    """)

    # Seed the real validated sample video from Phase 1
    video_id = "local-test-sample"
    cur.execute("""
    INSERT OR REPLACE INTO discovered_videos (
        id, workspace_id, source_id, external_id, title, channel_title, url, 
        published_at, category, rights_status, rights_notes, local_media_path
    ) VALUES (?, 'ws-default', ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?);
    """, (
        video_id,
        "local-upload",
        "test_sample.mp4",
        "Autonomous Viral Short Form Video Production",
        "HypeNova Studio (Creator Owned)",
        "C:\\Users\\shash\\Downloads\\Youtube\\test_sample.mp4",
        "gaming",
        "AUTHORIZED",
        "Verified creator-owned benchmark asset. Fully rights cleared.",
        "C:\\Users\\shash\\Downloads\\Youtube\\test_sample.mp4"
    ))

    # Seed the real rendered 9:16 vertical clip
    clip_id = "clip-01-autonomous-pipeline"
    score_breakdown = {
        "hook_strength": 19.0,
        "narrative_completion": 19.5,
        "emotional_impact": 14.0,
        "visual_significance": 14.5,
        "standalone_clarity": 10.0,
        "audio_quality": 9.5,
        "trend_relevance": 9.0,
        "total": 95.5
    }
    post_meta = {
        "youtube": {
            "title": "Autonomous Short-Form Content Engine | HypeNova AI",
            "description": "Full end-to-end pipeline test from audio transcription to 9:16 vertical render.\n#AI #Shorts #Tech"
        },
        "instagram": {
            "caption": "From moments to momentum: testing autonomous vertical short-form editing with HypeNova AI. #AI #ContentCreation #Reels"
        },
        "facebook": {
            "caption": "Autonomous short-form video production pipeline test."
        }
    }

    cur.execute("""
    INSERT OR REPLACE INTO clips (
        id, workspace_id, video_id, title, hook, start_time, end_time, duration,
        viral_score, score_breakdown, preset, status, video_path, srt_path,
        post_metadata, qa_status
    ) VALUES (?, 'ws-default', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        clip_id,
        video_id,
        "Autonomous Short Form Pipeline",
        "Welcome to Hype Novel AI.",
        0.0,
        20.9,
        18.81,
        95.5,
        json.dumps(score_breakdown),
        "Indian Gaming Comedy",
        "APPROVED",
        "C:\\Users\\shash\\Downloads\\Youtube\\ClipKaro\\output\\test-sample\\edited\\01-autonomous-short-form-pipeline.mp4",
        "C:\\Users\\shash\\Downloads\\Youtube\\ClipKaro\\output\\test-sample\\edited\\01-autonomous-short-form-pipeline.srt",
        json.dumps(post_meta),
        "PASSED (-14.3 LUFS)"
    ))

    # Seed production cost entry
    cur.execute("""
    INSERT OR REPLACE INTO production_costs (
        id, workspace_id, clip_id, compute_seconds, storage_mb, api_tokens, cost_inr
    ) VALUES (?, 'ws-default', ?, ?, ?, ?, ?);
    """, (
        "cost-benchmark-1",
        clip_id,
        55.0,
        3.45,
        0,
        2.50 # Less than 3 rupees electricity / compute
    ))

    # Seed a sample client package for Creator Services
    cur.execute("""
    INSERT OR REPLACE INTO clients (
        id, workspace_id, client_name, contact_email, package_tier, monthly_rate_inr, clips_delivered_this_month, status
    ) VALUES (?, 'ws-default', ?, ?, ?, ?, ?, ?);
    """, (
        "client-demo-1",
        "Rift Gaming India",
        "partner@riftgaming.in",
        "30_CLIPS",
        25000,
        1,
        "ACTIVE"
    ))

    conn.commit()
    conn.close()
    log_event("Database", "Database initialized and initial benchmark data seeded successfully.")
    print("[ok] Initial database & benchmark clip seeded successfully.")

if __name__ == "__main__":
    seed()
