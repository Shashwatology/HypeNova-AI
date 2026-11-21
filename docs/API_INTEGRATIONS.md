# HypeNova AI — External API Integrations & Quota Engineering

## 1. Overview & Architectural Boundaries

HypeNova AI connects to Google and third-party APIs for discovery, publishing, performance analytics, and visual generation. Because third-party APIs enforce strict rate limits, credit billing, and data latency, this document outlines our integration specifications, quota calculations, and caching strategies.

---

## 2. YouTube Data API v3 — Quota Engineering & Publishing

### The Quota Reality
Every Google Cloud project receives a default allocation of **10,000 quota units per day** (resets daily at midnight Pacific Time).

| YouTube API Operation | Endpoint | Quota Cost per Call | Max Calls / Day (on 10,000 quota) |
| :--- | :--- | :---: | :---: |
| **Video Upload** | `POST /upload/youtube/v3/videos?part=snippet,status` | **1,600 units** | **6 uploads/day** |
| **Search Queries** | `GET /youtube/v3/search` | **100 units** | 100 searches/day |
| **Video Metadata Lookup** | `GET /youtube/v3/videos?part=snippet,statistics` | **1 unit** | 10,000 lookups/day |
| **Channel Information** | `GET /youtube/v3/channels?part=snippet` | **1 unit** | 10,000 lookups/day |
| **Playlist Items** | `GET /youtube/v3/playlistItems` | **1 unit** | 10,000 lookups/day |

### Quota Preservation Strategy
> [!IMPORTANT]
> **Zero-Quota Discovery**: HypeNova AI never uses `search.list` (100 units/call) for general content discovery.
> 1. **Public Feeds**: Channel updates are polled via YouTube RSS feeds (`https://www.youtube.com/feeds/videos.xml?channel_id={id}`), which consume **0 Google API quota units**.
> 2. **Targeted Lookups**: When metadata refresh is necessary, `videos.list` (1 unit) is called with batched IDs (up to 50 IDs per call).
> 3. **Quota Allocation**: 96% of our daily 10,000 units are reserved strictly for authenticated video publishing (`videos.insert`), allowing 6 verified Short uploads per day per free Google Cloud project.
> 4. **Higher Volume**: For agency workspaces managing 10+ channels, instructions are provided to request a quota increase from Google Cloud Console (Audit Tier: 250,000 to 1,000,000 units/day).

### Resumable Upload Architecture
All video uploads use the YouTube Resumable Upload protocol to guarantee fault tolerance over flaky network connections:
```python
def resumable_upload(youtube_client, file_path, metadata):
    media = MediaFileUpload(
        file_path,
        chunksize=1024 * 1024 * 4,  # 4MB chunks
        resumable=True,
        mimetype="video/mp4"
    )
    request = youtube_client.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "categoryId": "20"  # Gaming
            },
            "status": {
                "privacyStatus": metadata.get("privacy", "private"),  # Private initial state
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log_event("Publisher", f"Uploaded {int(status.progress() * 100)}%")
    return response["id"]
```

---

## 3. YouTube Analytics API — SlAs & Latency Realities

### The 48–72 Hour Aggregation Latency
> [!WARNING]
> **Official Latency Notice**: As documented in Google's official YouTube Analytics API specification, authenticated performance metrics (such as audience retention curves, traffic sources, and demographics) are subject to a **48 to 72 hour processing latency**.

HypeNova AI enforces strict honesty in its UI:
1. **No Fake Real-Time Engagement**: When zero videos are published or a video is under 48 hours old, the dashboard displays clear empty/syncing states rather than fabricating live viewer curves.
2. **Experimental Benchmarks**: Format performance benchmarks (e.g., "GTA Chaos 82% retention") are clearly labeled as observational creator research benchmarks, distinct from the channel's authenticated API data.

### Analytics Query Parameters
```python
def fetch_authenticated_retention(analytics_client, channel_id, start_date, end_date):
    return analytics_client.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date.strftime("%Y-%m-%d"),
        endDate=end_date.strftime("%Y-%m-%d"),
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
        dimensions="video",
        sort="-views",
        maxResults=50
    ).execute()
```

---

## 4. PostKaro Bridge & Distribution Schema

HypeNova AI produces distribution-ready post packages fully compatible with [PostKaro](https://github.com/allthingsaman/PostKaro.git).

### The Standardized Postkit Schema (`post.json`)
```json
{
  "version": "1.0.0",
  "source_system": "HypeNova AI",
  "clip_id": "clip-01",
  "workspace_id": "ws-clutchrush",
  "media": {
    "file_path": "c:/Users/shash/Downloads/Youtube/output/test-sample/edited/01-autonomous-short-form-pipeline.mp4",
    "resolution": "1080x1920",
    "aspect_ratio": "9:16",
    "duration_seconds": 18.81,
    "loudness_lufs": -14.3
  },
  "distribution": {
    "platforms": ["youtube_shorts"],
    "target_channel": "ClutchRush Gaming",
    "scheduled_timestamp_utc": "2026-11-21T18:00:00Z"
  },
  "metadata": {
    "titles": [
      "I Tried Running an Autonomous AI Channel... 😳",
      "They Said AI Couldn't Edit Videos... Watch This!",
      "How to Make 100 Shorts Without Touching an Editor ⚡",
      "Is This the Future of YouTube Gaming?",
      "Autonomous Content Pipeline Test [RAW FOOTAGE]"
    ],
    "selected_title": "I Tried Running an Autonomous AI Channel... 😳 #Shorts",
    "description": "Full autonomous AI short-form pipeline demonstration.\n\nSubscribe for daily gaming highlights and AI automation experiments!\n\n#gaming #ai #shorts #technology",
    "tags": ["shorts", "gaming", "ai", "automation", "tech", "clutchrush"],
    "pinned_comment": "Which editing style do you prefer? Let me know in the comments below!"
  },
  "quality_assurance": {
    "lufs_verified": true,
    "blank_frames_detected": 0,
    "safe_zones_compliant": true
  }
}
```

---

## 5. Visual Generation — Gemini & Nano Banana

To ensure brand visual uniqueness without copyright strikes on thumbnail assets, HypeNova AI integrates with Google Gemini / Nano Banana for asset generation.

### Capabilities:
1. **Dynamic Hook Banners**: High-contrast, top-third text hook graphic banners rendered above video gameplay.
2. **Avatar Artwork**: Stylized channel avatar and banner creation for new publishing channels.
3. **Thumbnail Overlays**: Keyframe extraction merged with bold typography and emotion-exaggerating border elements.
