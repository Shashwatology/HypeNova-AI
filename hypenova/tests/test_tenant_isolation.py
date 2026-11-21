"""HypeNova AI - Multi-Tenant Isolation & Security Test Suite (Unittest)

Tests verify:
1. Cross-tenant access is strictly denied (HTTP 403 Forbidden).
2. Data isolation between workspaces (accounts, clips, discoveries, costs).
3. Token authentication and workspace membership validation.
4. Prevention of unauthorized clip editing across tenant boundaries.
"""
import unittest
from starlette.testclient import TestClient
from hypenova.api.server import app
from hypenova.database import get_connection, init_db

class TestTenantIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Seeds two isolated users with their own private workspaces."""
        init_db()
        conn = get_connection()
        cur = conn.cursor()

        # Tenant A (Alice)
        cur.execute("INSERT OR REPLACE INTO users (id, email, display_name) VALUES ('usr-alice', 'alice@gaming.io', 'Alice Streamer');")
        cur.execute("INSERT OR REPLACE INTO workspaces (id, name, slug, owner_user_id, tier) VALUES ('ws-alice-studio', 'Alice Gaming Studio', 'ws-alice', 'usr-alice', 'CREATOR');")
        cur.execute("INSERT OR REPLACE INTO workspace_members (id, workspace_id, user_id, role) VALUES ('mem-alice-1', 'ws-alice-studio', 'usr-alice', 'OWNER');")

        # Tenant B (Bob)
        cur.execute("INSERT OR REPLACE INTO users (id, email, display_name) VALUES ('usr-bob', 'bob@podcast.io', 'Bob Founder');")
        cur.execute("INSERT OR REPLACE INTO workspaces (id, name, slug, owner_user_id, tier) VALUES ('ws-bob-studio', 'Bob Podcast Media', 'ws-bob', 'usr-bob', 'CREATOR');")
        cur.execute("INSERT OR REPLACE INTO workspace_members (id, workspace_id, user_id, role) VALUES ('mem-bob-1', 'ws-bob-studio', 'usr-bob', 'OWNER');")

        # Add private YouTube account to Alice's workspace
        cur.execute("""
        INSERT OR REPLACE INTO connected_accounts (id, workspace_id, platform, account_email, channel_id, channel_title, status)
        VALUES ('acc-alice-yt', 'ws-alice-studio', 'youtube', 'alice@gaming.io', 'UC_ALICE_PRIVATE', 'Alice Highlights', 'CONNECTED');
        """)

        # Add private YouTube account to Bob's workspace
        cur.execute("""
        INSERT OR REPLACE INTO connected_accounts (id, workspace_id, platform, account_email, channel_id, channel_title, status)
        VALUES ('acc-bob-yt', 'ws-bob-studio', 'youtube', 'bob@podcast.io', 'UC_BOB_PRIVATE', 'Bob Deep Dives', 'CONNECTED');
        """)

        # Add source and discovered video for Alice
        cur.execute("""
        INSERT OR IGNORE INTO sources (id, workspace_id, name, source_type, identifier, category)
        VALUES ('src-alice', 'ws-alice-studio', 'Alice Raw Stream', 'local', 'alice_stream.mp4', 'gaming');
        """)
        cur.execute("""
        INSERT OR REPLACE INTO discovered_videos (id, workspace_id, source_id, title, url, rights_status)
        VALUES ('vid-test-01', 'ws-alice-studio', 'src-alice', 'Alice GTA 5 Session', 'http://localhost/alice.mp4', 'AUTHORIZED');
        """)

        # Add source and discovered video for Bob
        cur.execute("""
        INSERT OR IGNORE INTO sources (id, workspace_id, name, source_type, identifier, category)
        VALUES ('src-bob', 'ws-bob-studio', 'Bob Founder Talks', 'local', 'bob_talks.mp4', 'podcast');
        """)
        cur.execute("""
        INSERT OR REPLACE INTO discovered_videos (id, workspace_id, source_id, title, url, rights_status)
        VALUES ('vid-test-02', 'ws-bob-studio', 'src-bob', 'Bob 10M MRR Breakdown', 'http://localhost/bob.mp4', 'AUTHORIZED');
        """)

        # Add private clip to Alice
        cur.execute("""
        INSERT OR REPLACE INTO clips (id, workspace_id, video_id, title, hook, start_time, end_time, duration, viral_score, status)
        VALUES ('clip-alice-01', 'ws-alice-studio', 'vid-test-01', 'Alice Insane GTA Clutch', 'Look at this jump!', 0.0, 15.0, 15.0, 88, 'EDITED');
        """)

        # Add private clip to Bob
        cur.execute("""
        INSERT OR REPLACE INTO clips (id, workspace_id, video_id, title, hook, start_time, end_time, duration, viral_score, status)
        VALUES ('clip-bob-01', 'ws-bob-studio', 'vid-test-02', 'Bob Secret to 10M MRR', 'Stop doing meetings!', 10.0, 30.0, 20.0, 92, 'EDITED');
        """)

        conn.commit()
        conn.close()

    def setUp(self):
        self.client = TestClient(app)

    def test_01_alice_can_access_own_workspace(self):
        """Alice should successfully read overview from her own workspace."""
        headers = {
            "Authorization": "Bearer dev-token-usr-alice",
            "X-Workspace-Id": "ws-alice-studio"
        }
        res = self.client.get("/api/overview", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["workspace"]["id"], "ws-alice-studio")
        self.assertEqual(data["workspace"]["name"], "Alice Gaming Studio")

    def test_02_bob_forbidden_from_alice_workspace(self):
        """Bob must be strictly BLOCKED with HTTP 403 when trying to access Alice's workspace."""
        headers = {
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-alice-studio"
        }
        res = self.client.get("/api/overview", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied", res.json()["detail"])

    def test_03_connected_accounts_data_isolation(self):
        """Alice and Bob must ONLY see their own connected YouTube channels."""
        # Alice's view
        res_alice = self.client.get("/api/accounts", headers={
            "Authorization": "Bearer dev-token-usr-alice",
            "X-Workspace-Id": "ws-alice-studio"
        })
        self.assertEqual(res_alice.status_code, 200)
        alice_accounts = res_alice.json()["accounts"]
        self.assertEqual(len(alice_accounts), 1)
        self.assertEqual(alice_accounts[0]["channel_id"], "UC_ALICE_PRIVATE")
        self.assertEqual(alice_accounts[0]["channel_title"], "Alice Highlights")

        # Bob's view
        res_bob = self.client.get("/api/accounts", headers={
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-bob-studio"
        })
        self.assertEqual(res_bob.status_code, 200)
        bob_accounts = res_bob.json()["accounts"]
        self.assertEqual(len(bob_accounts), 1)
        self.assertEqual(bob_accounts[0]["channel_id"], "UC_BOB_PRIVATE")
        self.assertEqual(bob_accounts[0]["channel_title"], "Bob Deep Dives")

    def test_04_clips_isolation_between_workspaces(self):
        """Alice's clips must not be visible to Bob."""
        res_alice = self.client.get("/api/clips", headers={
            "Authorization": "Bearer dev-token-usr-alice",
            "X-Workspace-Id": "ws-alice-studio"
        })
        self.assertEqual(res_alice.status_code, 200)
        clips_alice = [c["id"] for c in res_alice.json()["clips"]]
        self.assertIn("clip-alice-01", clips_alice)
        self.assertNotIn("clip-bob-01", clips_alice)

        res_bob = self.client.get("/api/clips", headers={
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-bob-studio"
        })
        self.assertEqual(res_bob.status_code, 200)
        clips_bob = [c["id"] for c in res_bob.json()["clips"]]
        self.assertIn("clip-bob-01", clips_bob)
        self.assertNotIn("clip-alice-01", clips_bob)

    def test_05_cannot_tamper_with_other_tenant_clip_timeline(self):
        """Bob cannot edit or retrieve Alice's clip timeline."""
        headers = {
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-bob-studio"
        }
        # Bob requests timeline for Alice's clip within Bob's workspace header -> clip not in Bob's workspace (404)
        res = self.client.get("/api/editor/timeline/clip-alice-01", headers=headers)
        self.assertEqual(res.status_code, 404)

        # Bob tries to pass Alice's workspace header -> 403 Forbidden
        res_forbidden = self.client.get("/api/editor/timeline/clip-alice-01", headers={
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-alice-studio"
        })
        self.assertEqual(res_forbidden.status_code, 403)

    def test_06_cross_tenant_channel_disconnect_blocked(self):
        """Bob cannot disconnect Alice's channel."""
        # Bob attempts to disconnect Alice's channel in Bob's workspace
        res = self.client.post("/api/accounts/acc-alice-yt/disconnect", headers={
            "Authorization": "Bearer dev-token-usr-bob",
            "X-Workspace-Id": "ws-bob-studio"
        })
        self.assertEqual(res.status_code, 200)
        
        # Verify Alice's channel is STILL intact in Alice's workspace
        res_alice = self.client.get("/api/accounts", headers={
            "Authorization": "Bearer dev-token-usr-alice",
            "X-Workspace-Id": "ws-alice-studio"
        })
        self.assertEqual(len(res_alice.json()["accounts"]), 1)
        self.assertEqual(res_alice.json()["accounts"][0]["id"], "acc-alice-yt")

if __name__ == "__main__":
    unittest.main()
