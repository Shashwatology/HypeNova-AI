"""HypeNova AI - Multi-Channel Profile & Rights Management"""
import json
from typing import Dict, List, Optional
from hypenova.config import DEFAULT_CHANNELS
from hypenova.database import get_connection, log_event

class ChannelManager:
    """Manages channel identities, daily limits, and posting permissions."""

    def __init__(self):
        self.init_channels()

    def init_channels(self):
        conn = get_connection()
        cur = conn.cursor()
        for ch in DEFAULT_CHANNELS:
            cur.execute("""
            INSERT OR IGNORE INTO channel_profiles (id, name, platform, publish_mode, daily_limit, settings_json)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (ch["id"], ch["name"], ch["platform"], ch["publish_mode"], ch["daily_limit"], json.dumps(ch)))
        conn.commit()
        conn.close()

    def get_all_channels(self) -> List[Dict]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM channel_profiles;")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_channel(self, channel_id: str) -> Optional[Dict]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM channel_profiles WHERE id = ?;", (channel_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_publish_mode(self, channel_id: str, new_mode: str):
        """Switches between MANUAL and AUTO_AUTHORIZED_ONLY."""
        conn = get_connection()
        conn.execute("UPDATE channel_profiles SET publish_mode = ? WHERE id = ?;", (new_mode, channel_id))
        conn.commit()
        conn.close()
        log_event("ChannelManager", f"Channel {channel_id} publish mode updated to {new_mode}")
