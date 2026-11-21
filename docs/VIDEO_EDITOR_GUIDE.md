# HypeNova AI — Multi-Track Video Editor & Subtitle Guide

## 1. Architectural Philosophy & Engine Design

When architecting the video editor for HypeNova AI, open-source video libraries were carefully evaluated against legal and technical constraints:
- **OpenVideo Editor**: Dual-licensed under GPL-3.0 copyleft, which legally threatens proprietary SaaS codebases.
- **Remotion**: Excellent for programmatic React rendering, but incurs substantial per-seat commercial enterprise license fees for businesses exceeding revenue thresholds.

### The HypeNova Native Canvas + FFmpeg Engine
HypeNova AI uses a lightweight, non-destructive **HTML5 Canvas / Multi-Track Web UI** coupled to **ClipKaro's MIT-licensed FFmpeg rendering pipeline**:
1. **Interactive Timeline**: Renders video, normalized audio waveforms, and word-level caption blocks in real time with sub-10ms scrubbing response.
2. **Safe-Area Guidance**: Renders visual bounding overlays preventing captions from colliding with YouTube Shorts UI buttons.
3. **Non-Destructive Drafts**: Edits (In-Points, Out-Points, caption text, preset choices) are persisted as JSON drafts in the database without altering source footage.
4. **Deterministic FFmpeg Compiling**: Clicking "Re-Render & Export" translates the timeline parameters directly into FFmpeg filtergraphs for production rendering.

---

## 2. Multi-Track Timeline Layout

```
+----------------------------------------------------------------------------------------------------+
|  [ 00:00.00 / 00:18.81 ]   [ Set In [ ]   [ Set Out ] ]   [ ✂️ Split ]   [ ↩ Undo ]   [ ↪ Redo ]    |
+----------------------------------------------------------------------------------------------------+
| TIME RULER   |  .  .  .  .  |  .  .  .  .  |  .  .  .  .  |  .  .  .  .  |  .  .  .  .  | [PLAYHEAD]|
+----------------------------------------------------------------------------------------------------+
| TRACK 1      | [TRIM-L]  01-autonomous-short-form-pipeline.mp4                    [TRIM-R]        |
| (VIDEO 9:16) |                                                                                     |
+----------------------------------------------------------------------------------------------------+
| TRACK 2      | ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| |
| (AUDIO -14L) | Target Loudness: -14.3 LUFS Normalized                                              |
+----------------------------------------------------------------------------------------------------+
| TRACK 3      | [WELCOME] [HYPE NOVEL] [AI] [TODAY WE] [ARE TESTING] [AUTONOMOUS] [VIRAL SHORT]     |
| (CAPTIONS)   | Word-by-word animated karaoke blocks with click-to-edit inspector                  |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Timeline Editing Operations

### A. Scrubbing & Playhead Control
- **Ruler Seeking**: Click anywhere along the top time ruler to immediately seek the video player to that timestamp.
- **Playhead Tracking**: As the video plays, the cyan playhead moves across all three tracks in real time.
- **Precision Stepping**: Use the `⏪` and `⏩` buttons to step forward or backward by 0.5-second increments.

### B. Trimming & Boundary Adjustments
- **Drag-Trimming**: Click and drag the left cyan handle (`handle-trim-left`) to adjust the clip In-Point. Drag the right handle (`handle-trim-right`) to adjust the Out-Point.
- **Quick Snapping**:
  - `Set In-Point [`: Snaps the start time directly to current playhead position.
  - `Set Out-Point ]`: Snaps the end time directly to current playhead position.
- **Splitting**: Click `✂️ Split at Playhead` to create an edit partition mark at the exact timecode.

### C. Undo & Redo History Stack
Every trimming change, caption edit, or preset selection pushes state onto `historyStack`.
- Click `↩ Undo` to revert to previous trim and caption states.
- Click `↪ Redo` to re-apply undone changes.

---

## 4. Word-Level Caption Editing (Track 3)

HypeNova AI automatically aligns word-level subtitles generated via Whisper ASR into editable timeline blocks.

### Interactive Subtitle Workflow:
1. **Selection**: Click on any caption block on Track 3. The block highlights with a vivid violet border.
2. **Inspector Panel**: The right-hand Caption Inspector automatically populates:
   - **Active Word / Phrase**: Edit misspelled slang, creator tags, or Hinglish phrases.
   - **Start Time (s)**: Adjust onset timing down to the tenth of a second.
   - **End Time (s)**: Adjust offset timing.
3. **Commit**: Click `Update Caption`. The block updates in the timeline, pushes to the undo history stack, and persists.
4. **Live Karaoke Tracking**: When playing the video, the caption block corresponding to the current spoken word highlights in solid violet with glow.

---

## 5. Safe Area Overlays & Aspect Ratio Control

Mobile short-form video apps (YouTube Shorts, Instagram Reels, TikTok) overlay persistent UI elements on top of the video canvas. Content placed in these areas is obscured.

### Safe Zones Visualized:
- **Top Safe Zone (Red, 50px / 200px equivalent)**: Keeps top hooks below channel search bars and status icons.
- **Right Safe Zone (Amber, 48px)**: Prevents graphics from being blocked by the Like, Dislike, Comment, and Share action buttons.
- **Bottom Safe Area (Violet, 80px / 320px equivalent)**: Ensures high-retention karaoke captions stay above the channel avatar, handle, title, and sound attribution bar.

Toggle the **Safe Area Guides** switch in the left inspector to preview the exact mobile viewport overlay.

---

## 6. Visual Presets & Sound Design

Choose from 6 battle-tested editing presets in the dropdown:

1. **Indian Gaming Comedy**: High-contrast yellow/white captions, Hinglish word highlights, funny laugh tracks, whoosh SFX, spontaneous zooms on streamer webcam.
2. **GTA Chaos**: Rapid jump-cuts removing dead pauses (>0.3s), karaoke word popups, bass drop on vehicle collisions, high-saturation color grading.
3. **Clean Podcast**: Elegant centered monochrome captions, subtle blur background for landscape footage, restrained sub-bass accents.
4. **Cinematic Gaming**: Letterbox pacing, dramatic orchestral swells, slow zoom into pivotal storyline moments.
5. **Quick News**: High-contrast top hook box with headline, rapid subtitle pacing, ticker tape branding.
6. **Minimal Viral**: Mobile-first vertical reframing, zero extraneous SFX, crisp voice normalization.

---

## 7. Re-Rendering & Export

1. Once trimming and subtitle corrections are finalized, click **🚀 Re-Render & Export**.
2. The UI sends a `TimelineSaveRequest` to `POST /api/editor/rerender`.
3. The backend executes FFmpeg filtergraphs compiling:
   - New In-Point and Out-Point video slicing.
   - Updated ASS subtitle formatting.
   - Audio normalization to **-14.0 LUFS**.
4. The QA badge updates to **QA Verified (-14.3 LUFS)**, and the video player immediately reloads the newly rendered short.
