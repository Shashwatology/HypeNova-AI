# Open-Source Research & Tool Selection Matrix
**Project**: HypeNova AI SaaS Transformation  
**Date**: November 2026

---

## 1. Candidate Technology Evaluation

| Component | Repository / Service | Licence | Commercial SaaS Usability | Strengths | Limitations & Risks | Architectural Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ASR & Video Processing** | [ClipKaro](https://github.com/allthingsaman/ClipKaro) | **MIT** | **Permitted** (100% free and open) | Faster-whisper on CPU/GPU, word-level timestamps, Hinglish Roman captions, YuNet face detection, pause-cutting, loudness normalization (-14 LUFS). | Local execution model; needs wrapper for multi-tenant cloud queue. | **Retain as Primary Processing Worker**. Proven, reliable, and tested on our machine. |
| **Publishing Integration** | [PostKaro](https://github.com/allthingsaman/PostKaro) | **MIT** | **Permitted** (Client code MIT) | Platform scheduling schema (`post.json`), multi-account model, desktop notification, retry workflows. | Designed for local desktop with OS keyring storage; cannot be used as a shared multi-tenant database directly. | **Adopt Schema & Workflow Concepts**. Implement multi-tenant encrypted database token storage for SaaS. |
| **AI Shorts Platform** | [OpenShorts](https://github.com/mutonby/openshorts) | Multi-license (Cloud directory proprietary) | **Restricted** (Cloud code non-commercial) | Web platform architecture, Shorts UI templates. | Cloud directory has restrictive custom license prohibiting commercial SaaS reuse. | **Do Not Copy Proprietary Code**. Ingest visual concepts only. |
| **Sentence-Based Trimming** | [ClipsAI](https://github.com/ClipsAI/clipsai) | **MIT** | **Permitted** | Clean Python algorithms for speech boundary detection and speaker reframing. | Slower updates; heavy dependencies. | **Reference for algorithmic boundary snapping**. |
| **Browser Video Editor** | [OpenVideo Editor](https://github.com/openvideodev/react-video-editor) | GPL-3.0 / Commercial | **Restricted under GPL** (Forces open source or paid license) | Multi-track timeline, visual waveform, canvas scrubbing, crop handles. | Strong copyleft license (GPL-3.0) requires entire SaaS frontend to be open-sourced if bundled. | **Build Native Clean Timeline Component**. Construct a bespoke HTML5/Canvas/CSS multi-track timeline directly in HypeNova UI without GPL copyleft taint. |
| **React Video Rendering** | [Remotion](https://www.remotion.dev/) | Remotion License | **Free for <$3M rev / <3 employees; Paid for larger enterprise** | React-based programmatic video generation, high customization. | Heavy Node.js footprint in video workers; enterprise license restrictions. | **Keep as Optional Secondary Engine** (ClipKaro already includes optional Remotion bridge). Primary renderer remains Python + OpenCV + FFmpeg. |
| **User Identity & Auth** | [Firebase Authentication](https://firebase.google.com/docs/auth) | Google Cloud Terms | **Commercial SaaS Ready** (Generous free tier) | Sign in with Google, email/password, JWT ID tokens, session management, Firebase Admin SDK for Python. | Free tier limits monthly active users; requires external Google Cloud Project. | **Adopt for Application User Identity**. Segregate strictly from YouTube OAuth channel permissions. |
| **YouTube Video Upload** | [YouTube Data API v3](https://developers.google.com/youtube/v3) | Google Cloud API | **Official / Free Quota** | Official video upload (`videos.insert`), metadata update, privacy status (private/unlisted/public), tags, categories. | Daily quota: 10,000 units/day. Video upload costs 1,600 units (~6 uploads/day on default quota). Quota increase request needed for scale. | **Adopt as Official Upload Mechanism**. Implement private upload mode and idempotent duplicate guards. |
| **YouTube Performance** | [YouTube Analytics API](https://developers.google.com/youtube/analytics) | Google Cloud API | **Official / Free Quota** | Authenticated metrics: views, watch time, average view duration, likes, comments, subscriber changes. | **48–72 hour data reporting lag** as documented by Google. Does not report real-time seconds retention for newly posted clips. | **Adopt for Channel Reports**. Must clearly display "48-72h Processing Lag" on dashboard to prevent user confusion. |
| **Visual Art Generation** | [Google Gemini / Nano Banana](https://ai.google.dev/gemini-api/docs/image-generation) | Google Cloud / AI Studio | **Commercial API Ready** (Pay-per-use or free tier limits) | Generates original brand artwork, wordmark concepts, abstract gaming backgrounds, and thumbnail backdrops. | Requires Gemini API Key or Firebase Blaze plan. Must not copy copyrighted game assets or creator faces. | **Adopt for Original Graphic Asset Generation**. Configurable via API key; fallback to local procedural artwork when key is absent. |

---

## 2. Architectural Blueprint Decisions

1. **Clean Separation of Identity vs. Channel Permissions**:
   - `Firebase Auth ID Token`: Authenticates that the user is *John Doe* and grants access to *John Doe's Workspace*.
   - `Google YouTube OAuth Token`: Authenticates that *John Doe's Workspace* has permission to upload to YouTube Channel *ClutchRush Gaming*.
   - These tokens are stored in separate schemas. YouTube refresh tokens are encrypted at rest with server-side keys.
2. **Timeline Editor Architecture**:
   - Rather than bundling heavy GPL-licensed editors (like OpenVideo Editor) or incurring Remotion enterprise licensing, HypeNova implements a **native, responsive multi-track timeline** in modern JavaScript:
     - Track 1: Video Track (with visual frame blocks and drag-trim handles)
     - Track 2: Audio Waveform Track
     - Track 3: Subtitle/Caption Track (with individual word blocks, editable text, and timing readjustment)
   - The timeline state produces an exact `edit_spec.json` that maps 1:1 to ClipKaro's FFmpeg cutting and subtitle burning pipeline.
3. **Data Provenance & Rights Governance**:
   - Every video record maintains complete provenance: `original_url`, `channel_id`, `acquired_via` (RSS/Manual Upload), `rights_status`, and `rights_notes`.
   - Content without verified rights is blocked from publishing queues.
