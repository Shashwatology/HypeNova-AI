"""HypeNova AI - Autonomous Content Scout Engine (HypeScout)"""
import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from hypenova.config import DATA_DIR, UPLOADS_DIR
from hypenova.database import get_connection, log_event
from hypenova.scout.watchlists import CURATED_GAMING_SOURCES, CURATED_PODCAST_SOURCES

class HypeScout:
    """Discovers content opportunities from YouTube RSS feeds, APIs, and local creator uploads."""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")

    def seed_default_sources(self):
        """Seeds curated gaming and podcast watchlists into the database."""
        conn = get_connection()
        cur = conn.cursor()
        all_sources = CURATED_GAMING_SOURCES + CURATED_PODCAST_SOURCES
        for src in all_sources:
            cur.execute("""
            INSERT OR IGNORE INTO sources (id, name, source_type, identifier, category, language, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (src["id"], src["name"], src["source_type"], src["identifier"], src["category"], src["language"], src["notes"]))
        conn.commit()
        conn.close()
        log_event("HypeScout", f"Seeded {len(all_sources)} default creator watchlists.")

    def scan_all_sources(self) -> Dict[str, Any]:
        """Runs discovery scan across all enabled sources."""
        self.seed_default_sources()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sources WHERE enabled = 1;")
        sources = cur.fetchall()
        
        new_discoveries_count = 0
        scanned_count = len(sources)

        for src in sources:
            try:
                new_items = self.scan_source(dict(src))
                new_discoveries_count += new_items
            except Exception as e:
                log_event("HypeScout", f"Error scanning source {src['name']}: {str(e)}", "WARNING")

        # Also scan local uploads directory
        local_discoveries = self.scan_local_uploads()
        new_discoveries_count += local_discoveries

        conn.close()
        log_event("HypeScout", f"Scan complete. Scanned {scanned_count} sources, found {new_discoveries_count} new media items.")
        return {
            "scanned_sources": scanned_count,
            "new_discoveries": new_discoveries_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def scan_source(self, source: Dict) -> int:
        """Fetches videos from a source using YouTube RSS feeds (no API key required)."""
        identifier = source["identifier"]
        channel_id = identifier if not identifier.startswith("http") else self._extract_channel_id(identifier)
        if not channel_id:
            return 0

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        req = urllib.request.Request(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HypeNovaAI/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read()
            return self._parse_and_persist_rss(content, source)
        except Exception as e:
            # If network is unreachable or blocked, gracefully log and continue
            log_event("HypeScout", f"RSS fetch notice for {source['name']}: {str(e)}", "INFO")
            return 0

    def _parse_and_persist_rss(self, xml_content: bytes, source: Dict) -> int:
        root = ET.fromstring(xml_content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/"
        }

        conn = get_connection()
        cur = conn.cursor()
        new_items = 0

        for entry in root.findall("atom:entry", ns):
            video_id_el = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            published_el = entry.find("atom:published", ns)
            link_el = entry.find("atom:link", ns)

            if video_id_el is None or title_el is None:
                continue

            video_id = video_id_el.text
            title = title_el.text
            url = link_el.attrib.get("href", f"https://www.youtube.com/watch?v={video_id}")
            published_at = published_el.text if published_el is not None else datetime.now(timezone.utc).isoformat()

            # Deduplication
            cur.execute("SELECT id FROM discovered_videos WHERE external_id = ?;", (video_id,))
            if cur.fetchone():
                continue

            # Public engagement metrics from media group if available
            views = 0
            likes = 0
            community = entry.find("media:group/media:community", ns)
            if community is not None:
                stats = community.find("media:statistics", ns)
                if stats is not None and "views" in stats.attrib:
                    views = int(stats.attrib["views"])

            # Rights state: A discovered YouTube video is a reference; requires rights check or authorized media file
            rights_status = "DISCOVERED"
            rights_notes = f"Discovered via public channel feed {source['name']}. Source media or creator authorization required."

            record_id = f"yt-{video_id}"
            cur.execute("""
            INSERT INTO discovered_videos (id, source_id, external_id, title, channel_title, url, published_at, view_count, like_count, category, rights_status, rights_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (record_id, source["id"], video_id, title, source["name"], url, published_at, views, likes, source["category"], rights_status, rights_notes))
            
            new_items += 1

        # Update last checked timestamp
        cur.execute("UPDATE sources SET last_checked_at = ? WHERE id = ?;", (datetime.now(timezone.utc).isoformat(), source["id"]))
        conn.commit()
        conn.close()
        return new_items

    def scan_local_uploads(self) -> int:
        """Discovers authorized local files uploaded by creator into uploads directory."""
        if not UPLOADS_DIR.exists():
            return 0

        conn = get_connection()
        cur = conn.cursor()
        new_items = 0

        valid_exts = {".mp4", ".mov", ".mkv", ".webm"}
        for f in UPLOADS_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in valid_exts:
                file_hash = hashlib.md5(f.name.encode()).hexdigest()[:12]
                rec_id = f"local-{file_hash}"

                cur.execute("SELECT id FROM discovered_videos WHERE id = ?;", (rec_id,))
                if cur.fetchone():
                    continue

                # Local uploaded files are creator-provided -> AUTHORIZED for processing!
                cur.execute("""
                INSERT INTO discovered_videos (id, source_id, external_id, title, channel_title, url, published_at, category, rights_status, rights_notes, local_media_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    rec_id,
                    "local-upload",
                    f.name,
                    f.stem.replace("_", " ").title(),
                    "Creator Owned / Uploaded",
                    str(f),
                    datetime.now(timezone.utc).isoformat(),
                    "gaming",
                    "AUTHORIZED",
                    "Direct creator-authorized local file.",
                    str(f)
                ))
                new_items += 1

        conn.commit()
        conn.close()
        return new_items

    def update_rights_status(self, video_id: str, new_status: str, notes: str):
        """Updates rights status: DISCOVERED, SOURCE_REQUIRED, RIGHTS_REVIEW, AUTHORIZED, PROCESSING, READY_FOR_REVIEW, APPROVED, PUBLISHED, BLOCKED"""
        conn = get_connection()
        conn.execute("UPDATE discovered_videos SET rights_status = ?, rights_notes = ? WHERE id = ?;", (new_status, notes, video_id))
        conn.commit()
        conn.close()
        log_event("HypeScout", f"Rights status for video {video_id} updated to {new_status}: {notes}")

    def _extract_channel_id(self, url: str) -> Optional[str]:
        m = re.search(r"channel/([a-zA-Z0-9_-]+)", url)
        return m.group(1) if m else None
