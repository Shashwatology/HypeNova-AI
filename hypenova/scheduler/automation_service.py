"""HypeNova AI - Persistent Background Automation Service"""
import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Optional
from hypenova.config import DEFAULT_DISCOVERY_INTERVAL_HOURS, DEFAULT_QUEUE_UPDATE_INTERVAL_HOURS
from hypenova.database import get_connection, log_event
from hypenova.scout.scout_engine import HypeScout

class AutomationService:
    """Manages autonomous scheduled discovery, processing queues, and rights validation."""

    def __init__(self):
        self.scout = HypeScout()
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log_event("Automation", "Persistent automation service started in background.")

    def stop(self):
        self.running = False
        log_event("Automation", "Automation service stopped.")

    def _run_loop(self):
        log_event("Automation", "Execution loop initiated. Running initial discovery scan...")
        try:
            self.scout.scan_all_sources()
        except Exception as e:
            log_event("Automation", f"Initial discovery scan error: {str(e)}", "WARNING")

        last_discovery_time = time.time()
        discovery_interval_sec = DEFAULT_DISCOVERY_INTERVAL_HOURS * 3600

        while self.running:
            try:
                now = time.time()
                # Run Discovery Scan
                if (now - last_discovery_time) >= discovery_interval_sec:
                    log_event("Automation", "Triggering scheduled discovery scan...")
                    self.scout.scan_all_sources()
                    last_discovery_time = now

                # Run Queue & Rights Checker every 5 minutes
                self._check_processing_queue()

            except Exception as e:
                log_event("Automation", f"Loop exception: {str(e)}", "ERROR")

            time.sleep(30) # Poll interval

    def _check_processing_queue(self):
        """Checks for authorized media files ready for transcription and vertical rendering."""
        conn = get_connection()
        cur = conn.cursor()
        # Only process media explicitly marked AUTHORIZED
        cur.execute("SELECT * FROM discovered_videos WHERE rights_status = 'AUTHORIZED' AND local_media_path IS NOT NULL LIMIT 2;")
        items = cur.fetchall()
        for item in items:
            log_event("Automation", f"Found authorized video ready for pipeline: {item['title']} ({item['local_media_path']})")
        conn.close()

automation_service = AutomationService()
