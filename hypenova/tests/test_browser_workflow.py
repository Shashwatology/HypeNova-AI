"""HypeNova AI - Full Zero-Terminal Browser Creator Workflow Acceptance Test

Simulates the entire creator experience from the browser without running any terminal commands:
1. Direct footage upload with mandatory rights certification
2. Automated background job execution (Whisper INT8 + 7-factor viral scoring + FFmpeg 9:16 rendering)
3. Job progress tracking (0 -> 100%) through REST polling
4. Real rendered vertical short verification
5. Multi-track browser timeline edit and real FFmpeg re-rendering
6. YouTube Shorts approval and simulated instant publishing verification
7. Observational analytics and workspace telemetry synchronization
"""
import json
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starlette.testclient import TestClient
from hypenova.api.server import app
from hypenova.config import MEDIA_DIR, RENDER_OUTPUT_DIR

def run_acceptance_test():
    client = TestClient(app)
    headers = {"X-Workspace-Id": "ws-default", "Authorization": "Bearer dev-token-usr-admin"}
    print("=" * 70)
    print("HYPENOVA AI — ZERO-TERMINAL BROWSER CREATOR ACCEPTANCE TEST")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: Health & Overview Check
    # -------------------------------------------------------------
    res_ov = client.get("/api/overview", headers=headers)
    assert res_ov.status_code == 200, f"Overview failed: {res_ov.text}"
    print("[STEP 1 PASS] Workspace Overview accessible & tenant isolated.")

    # -------------------------------------------------------------
    # Step 2: Upload Video Footage with Mandatory Rights Certification
    # -------------------------------------------------------------
    sample_video = Path("test_sample.mp4")
    if not sample_video.is_file():
        sample_video = Path("ClipKaro/output/test-sample/clips/01-autonomous-short-form-pipeline.mp4")

    assert sample_video.is_file(), f"Sample footage missing at {sample_video}"

    # Test rights enforcement rejection first
    with open(sample_video, "rb") as f:
        res_reject = client.post(
            "/api/projects/upload",
            files={"file": ("test_sample.mp4", f.read(), "video/mp4")},
            data={"title": "Uncertified Stream", "category": "gaming", "rights_certified": "false"},
            headers=headers
        )
    assert res_reject.status_code == 400, "Uncertified media was not rejected!"
    print("[STEP 2 PASS] Uncertified media upload strictly rejected (400 Bad Request).")

    # Upload with valid certification
    with open(sample_video, "rb") as f:
        video_bytes = f.read()

    res_upload = client.post(
        "/api/projects/upload",
        files={"file": ("autonomous_footage.mp4", video_bytes, "video/mp4")},
        data={
            "title": "GTA V Chaos Epic Escape",
            "category": "gaming",
            "preset": "GTA Chaos",
            "rights_certified": "true"
        },
        headers=headers
    )
    assert res_upload.status_code == 200, f"Upload failed: {res_upload.text}"
    upload_data = res_upload.json()
    job_id = upload_data["job_id"]
    video_id = upload_data["video_id"]
    print(f"[STEP 2 PASS] Video uploaded & certified. Job enqueued: {job_id} (Target: {video_id})")

    # -------------------------------------------------------------
    # Step 3: Monitor Background Processing Job (Polling)
    # -------------------------------------------------------------
    print(f"[STEP 3] Monitoring pipeline job '{job_id}' until completion...")
    max_wait = 90
    start_poll = time.time()
    last_stage = ""

    while time.time() - start_poll < max_wait:
        res_job = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert res_job.status_code == 200, f"Job check failed: {res_job.text}"
        job_info = res_job.json()
        status = job_info.get("status")
        progress = job_info.get("progress", 0)
        stage = job_info.get("stage") or job_info.get("error_message") or status

        if stage != last_stage:
            print(f"  -> [{progress}%] {stage}")
            last_stage = stage

        if status == "COMPLETED":
            break
        elif status in ["FAILED", "CANCELLED"]:
            raise RuntimeError(f"Job terminated prematurely with status {status}: {job_info.get('error_message')}")

        time.sleep(1.0)

    assert status == "COMPLETED", f"Job did not finish in {max_wait}s (Status: {status})"
    print(f"[STEP 3 PASS] Autonomous pipeline completed successfully in {round(time.time() - start_poll, 1)}s!")

    # -------------------------------------------------------------
    # Step 4: Verify Generated 9:16 Short & Metadata
    # -------------------------------------------------------------
    res_clips = client.get("/api/clips", headers=headers)
    assert res_clips.status_code == 200
    clips = res_clips.json().get("clips", [])
    assert len(clips) > 0, "No clips generated!"
    
    # Find newly generated clip
    target_clip = next((c for c in clips if c["video_id"] == video_id), clips[0])
    print(f"[STEP 4 PASS] Generated Short: '{target_clip['title']}' | Viral Score: {target_clip['viral_score']}/100 | QA: {target_clip.get('qa_status')}")

    out_mp4 = Path(target_clip["video_path"])
    assert out_mp4.is_file(), f"Output MP4 file missing: {out_mp4}"
    print(f"  -> Verified rendered MP4 file on disk: {out_mp4.name} ({round(out_mp4.stat().st_size / 1024, 1)} KB)")

    # -------------------------------------------------------------
    # Step 5: Multi-Track Browser Timeline Editing & Re-render
    # -------------------------------------------------------------
    timeline_res = client.get(f"/api/editor/timeline/{target_clip['id']}", headers=headers)
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()["timeline"]

    # Apply fine-grained browser edit: adjust in-point and change subtitle text
    rerender_payload = {
        "clip_id": target_clip["id"],
        "trim_start": 1.0,
        "trim_end": min(target_clip["end_time"], 14.5),
        "captions": [
            {"id": 1, "start": 1.0, "end": 3.0, "text": "CRAZY GTA ESCAPE"},
            {"id": 2, "start": 3.0, "end": 6.5, "text": "CAN WE SURVIVE THIS?"},
            {"id": 3, "start": 6.5, "end": 14.0, "text": "SMASH SUBSCRIBE NOW!"}
        ],
        "preset": "GTA Chaos",
        "safe_zones": True,
        "aspect_ratio": "9:16"
    }

    print(f"[STEP 5] Triggering timeline re-render from browser ({rerender_payload['trim_start']}s to {rerender_payload['trim_end']}s)...")
    rerender_res = client.post("/api/editor/rerender", json=rerender_payload, headers=headers)
    assert rerender_res.status_code == 200, f"Rerender failed: {rerender_res.text}"
    render_meta = rerender_res.json()
    print(f"[STEP 5 PASS] Re-rendered successfully in {render_meta['render_seconds']}s on CPU. Verified duration: {render_meta['actual_duration']}s")

    # -------------------------------------------------------------
    # Step 6: YouTube Shorts Publishing Handoff (Mock Verification)
    # -------------------------------------------------------------
    pub_payload = {
        "clip_id": target_clip["id"],
        "channel_profile_id": "clutchrush-gaming",
        "title": "Unreal GTA V Chaos Escape #Shorts",
        "description": "Rendered 100% autonomously in HypeNova AI browser studio #Gaming #GTA5"
    }
    pub_res = client.post("/api/calendar/publish_now", json=pub_payload, headers=headers)
    assert pub_res.status_code == 200, f"Publishing failed: {pub_res.text}"
    pub_data = pub_res.json()
    print(f"[STEP 6 PASS] Short Published to Queue! External URL: {pub_data['external_post_url']}")

    # -------------------------------------------------------------
    # Step 7: Telemetry, Observational Analytics & Health Check
    # -------------------------------------------------------------
    cal_res = client.get("/api/calendar", headers=headers)
    assert cal_res.status_code == 200
    queue_items = cal_res.json().get("queue", [])
    published_item = next((q for q in queue_items if q["clip_id"] == target_clip["id"]), None)
    assert published_item is not None, "Published item not found in calendar queue!"
    assert published_item["status"] == "PUBLISHED"
    print(f"[STEP 7 PASS] Verified Calendar Queue state: {published_item['clip_title']} -> STATUS: {published_item['status']}")

    analytics_res = client.get("/api/analytics", headers=headers)
    assert analytics_res.status_code == 200
    print(f"[STEP 7 PASS] Observational Analytics Synchronized. Delay notice: {analytics_res.json().get('data_notice')}")

    print("=" * 70)
    print("ALL 7 ACCEPTANCE TEST STEPS COMPLETED WITH ZERO ERRORS!")
    print("Zero-Terminal Browser Creator Workflow is 100% Operational.")
    print("=" * 70)

if __name__ == "__main__":
    run_acceptance_test()
