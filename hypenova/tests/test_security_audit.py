"""HypeNova AI - Security & Vulnerability Test Suite

Tests verify:
1. Production mode enforcement: dev-token-* rejection & missing token rejection.
2. Cross-tenant media streaming protection (cannot stream other workspace's clip).
3. OAuth CSRF state parameter validation (replay & forgery prevention).
4. Workspace ownership enforcement on all actions.
"""
import os
import unittest
from starlette.testclient import TestClient
from hypenova.api.server import app
from hypenova.database import get_connection, init_db

class TestSecurityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        conn = get_connection()
        cur = conn.cursor()

        # Seed Alice (ws-sec-alice) and Bob (ws-sec-bob)
        cur.execute("INSERT OR REPLACE INTO users (id, email, display_name) VALUES ('usr-sec-alice', 'alice@sec.io', 'Alice Sec');")
        cur.execute("INSERT OR REPLACE INTO workspaces (id, name, slug, owner_user_id, tier) VALUES ('ws-sec-alice', 'Alice Sec Studio', 'ws-sec-alice', 'usr-sec-alice', 'CREATOR');")
        cur.execute("INSERT OR REPLACE INTO workspace_members (id, workspace_id, user_id, role) VALUES ('mem-sec-alice', 'ws-sec-alice', 'usr-sec-alice', 'OWNER');")

        cur.execute("INSERT OR REPLACE INTO users (id, email, display_name) VALUES ('usr-sec-bob', 'bob@sec.io', 'Bob Sec');")
        cur.execute("INSERT OR REPLACE INTO workspaces (id, name, slug, owner_user_id, tier) VALUES ('ws-sec-bob', 'Bob Sec Studio', 'ws-sec-bob', 'usr-sec-bob', 'CREATOR');")
        cur.execute("INSERT OR REPLACE INTO workspace_members (id, workspace_id, user_id, role) VALUES ('mem-sec-bob', 'ws-sec-bob', 'usr-sec-bob', 'OWNER');")

        # Seed source & video
        cur.execute("INSERT OR IGNORE INTO sources (id, workspace_id, name, source_type, identifier, category) VALUES ('src-sec-alice', 'ws-sec-alice', 'Alice Video', 'local', 'test.mp4', 'gaming');")
        cur.execute("INSERT OR REPLACE INTO discovered_videos (id, workspace_id, source_id, title, url, rights_status, local_media_path) VALUES ('vid-sec-alice', 'ws-sec-alice', 'src-sec-alice', 'Alice GTA', 'http://local', 'AUTHORIZED', 'C:\\\\Users\\\\shash\\\\Downloads\\\\Youtube\\\\test_sample.mp4');")

        # Seed private clip for Alice
        cur.execute("""
        INSERT OR REPLACE INTO clips (id, workspace_id, video_id, title, hook, start_time, end_time, duration, viral_score, video_path, status)
        VALUES ('clip-sec-alice-99', 'ws-sec-alice', 'vid-sec-alice', 'Alice Private Highlight', 'Hook', 0.0, 10.0, 10.0, 90, 'C:\\\\Users\\\\shash\\\\Downloads\\\\Youtube\\\\test_sample.mp4', 'EDITED');
        """)

        conn.commit()
        conn.close()

    def setUp(self):
        self.client = TestClient(app)

    def test_01_production_mode_blocks_dev_tokens(self):
        """When HYPENOVA_ENV=production, dev-token-* MUST be rejected with HTTP 401."""
        os.environ["HYPENOVA_ENV"] = "production"
        try:
            res = self.client.get("/api/overview", headers={
                "Authorization": "Bearer dev-token-usr-sec-alice",
                "X-Workspace-Id": "ws-sec-alice"
            })
            self.assertEqual(res.status_code, 401)
            self.assertIn("Development tokens", res.json()["detail"])
        finally:
            os.environ.pop("HYPENOVA_ENV", None)

    def test_02_production_mode_blocks_unauthenticated_requests(self):
        """When HYPENOVA_ENV=production, requests without Authorization header must return HTTP 401."""
        os.environ["HYPENOVA_ENV"] = "production"
        try:
            res = self.client.get("/api/overview", headers={"X-Workspace-Id": "ws-sec-alice"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("Authentication required", res.json()["detail"])
        finally:
            os.environ.pop("HYPENOVA_ENV", None)

    def test_03_cross_tenant_media_streaming_blocked(self):
        """Bob cannot stream Alice's clip video file through the media API."""
        # Bob attempts to access Alice's clip using Bob's workspace header
        res = self.client.get("/api/media/clips/clip-sec-alice-99", headers={
            "Authorization": "Bearer dev-token-usr-sec-bob",
            "X-Workspace-Id": "ws-sec-bob"
        })
        self.assertEqual(res.status_code, 404)

        # Bob attempts to pass Alice's workspace header -> 403 Forbidden
        res_forbidden = self.client.get("/api/media/clips/clip-sec-alice-99", headers={
            "Authorization": "Bearer dev-token-usr-sec-bob",
            "X-Workspace-Id": "ws-sec-alice"
        })
        self.assertEqual(res_forbidden.status_code, 403)

    def test_04_oauth_state_generation_and_validation(self):
        """OAuth URL returns a valid CSRF state parameter that cannot be forged."""
        # 1. Alice requests OAuth URL
        res = self.client.get("/api/accounts/oauth/url", headers={
            "Authorization": "Bearer dev-token-usr-sec-alice",
            "X-Workspace-Id": "ws-sec-alice"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("oauth_url", data)
        self.assertIn("state_nonce", data)
        state_nonce = data["state_nonce"]

        # 2. Forged state parameter must be rejected
        forged_res = self.client.get(f"/api/accounts/oauth/callback?code=test-auth-code&state=forged-state-12345", headers={
            "Authorization": "Bearer dev-token-usr-sec-alice",
            "X-Workspace-Id": "ws-sec-alice"
        })
        self.assertEqual(forged_res.status_code, 400)
        self.assertIn("Invalid, expired, or forged", forged_res.json()["detail"])

        # 3. Legitimate state parameter succeeds
        valid_res = self.client.get(f"/api/accounts/oauth/callback?code=test-auth-code&state={state_nonce}", headers={
            "Authorization": "Bearer dev-token-usr-sec-alice",
            "X-Workspace-Id": "ws-sec-alice"
        })
        self.assertEqual(valid_res.status_code, 200)

        # 4. Replay attack: reusing the same state nonce must fail (one-time use)
        replay_res = self.client.get(f"/api/accounts/oauth/callback?code=test-auth-code&state={state_nonce}", headers={
            "Authorization": "Bearer dev-token-usr-sec-alice",
            "X-Workspace-Id": "ws-sec-alice"
        })
        self.assertEqual(replay_res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
