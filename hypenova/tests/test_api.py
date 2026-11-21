"""HypeNova AI - Integration API Endpoint Tests"""
import unittest
from starlette.testclient import TestClient
from hypenova.api.server import app

class TestHypeNovaAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_overview(self):
        res = self.client.get("/api/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("metrics", data)
        self.assertIn("system", data)
        self.assertGreaterEqual(data["metrics"]["clips_produced"], 1)

    def test_clips(self):
        res = self.client.get("/api/clips")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("clips", data)
        self.assertGreaterEqual(len(data["clips"]), 1)
        clip = data["clips"][0]
        self.assertIn("viral_score", clip)
        self.assertGreaterEqual(clip["viral_score"], 80.0)

    def test_presets(self):
        res = self.client.get("/api/presets")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("presets", data)
        self.assertIn("GTA Chaos", data["presets"])
        self.assertIn("Indian Gaming Comedy", data["presets"])

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")

    def test_business(self):
        res = self.client.get("/api/business")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("packages", data)
        self.assertEqual(len(data["packages"]), 3)

    def test_html_index(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("HypeNova", res.text)
        self.assertIn("From Moments to Momentum", res.text)

    def test_projects_upload_rights_enforcement(self):
        """Verifies that uncertified uploads are strictly rejected."""
        files = {"file": ("test.mp4", b"dummy video content", "video/mp4")}
        data = {"title": "Uncertified Video", "rights_certified": "false"}
        headers = {"X-Workspace-Id": "ws-default", "Authorization": "Bearer dev-token-usr-admin"}
        res = self.client.post("/api/projects/upload", files=files, data=data, headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Rights certification required", res.json()["detail"])

    def test_jobs_queue_and_lifecycle(self):
        """Tests job listing, creation, and progress inspection."""
        headers = {"X-Workspace-Id": "ws-default", "Authorization": "Bearer dev-token-usr-admin"}
        # List jobs
        res = self.client.get("/api/jobs", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("jobs", res.json())

        # Test project creation with authorized video
        create_payload = {
            "video_id": "vid-test-01",
            "preset": "Indian Gaming Comedy",
            "rights_certified": True
        }
        res_create = self.client.post("/api/projects/create", json=create_payload, headers=headers)
        if res_create.status_code == 200:
            job_id = res_create.json()["job_id"]
            # Inspect job status
            res_job = self.client.get(f"/api/jobs/{job_id}", headers=headers)
            self.assertEqual(res_job.status_code, 200)
            self.assertIn("progress", res_job.json())
            self.assertIn("stage", res_job.json())

    def test_publish_now_workflow(self):
        """Tests immediate publishing test verification."""
        headers = {"X-Workspace-Id": "ws-default", "Authorization": "Bearer dev-token-usr-admin"}
        # Fetch actual existing clip in workspace
        clips_res = self.client.get("/api/clips", headers=headers)
        self.assertEqual(clips_res.status_code, 200)
        clips = clips_res.json().get("clips", [])
        self.assertGreaterEqual(len(clips), 1)
        clip_id = clips[0]["id"]

        pub_payload = {
            "clip_id": clip_id,
            "channel_profile_id": "clutchrush-gaming",
            "title": "Autonomous GTA Chaos #Shorts",
            "description": "Rendered via HypeNova AI browser pipeline"
        }
        res = self.client.post("/api/calendar/publish_now", json=pub_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("https://youtube.com/shorts/", data["external_post_url"])

if __name__ == "__main__":
    unittest.main()
