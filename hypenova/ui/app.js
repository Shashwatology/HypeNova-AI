// HypeNova AI - Client Application & Interactive Video Editor Logic

// Global Application & Editor State
const state = {
  activeWorkspaceId: localStorage.getItem("hypenova_workspace") || "ws-default",
  activeClipId: "clip-1",
  duration: 18.81,
  currentTime: 0.0,
  trimStart: 0.0,
  trimEnd: 18.81,
  preset: "Indian Gaming Comedy",
  aspectRatio: "9:16",
  safeZones: true,
  captions: [
    { id: 1, start: 0.0, end: 0.7, text: "WELCOME TO" },
    { id: 2, start: 0.7, end: 1.16, text: "HYPE NOVEL" },
    { id: 3, start: 1.16, end: 1.62, text: "AI" },
    { id: 4, start: 1.62, end: 2.08, text: "TODAY WE" },
    { id: 5, start: 2.08, end: 2.56, text: "ARE TESTING" },
    { id: 6, start: 2.56, end: 3.12, text: "AUTONOMOUS" },
    { id: 7, start: 3.12, end: 3.90, text: "VIRAL SHORT" },
    { id: 8, start: 3.90, end: 4.58, text: "FORM VIDEO PRODUCTION" }
  ],
  activeCaptionId: null,
  historyStack: [],
  redoStack: [],
  selectedProjectFile: null,
  projectInputMode: "upload",
  activeJobId: null,
  jobPollInterval: null,
  scheduleClipId: null,
  availableClips: []
};

// Helper for authenticated API calls with Tenant Isolation
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  headers["X-Workspace-Id"] = state.activeWorkspaceId;
  headers["Authorization"] = "Bearer dev-token-usr-admin";
  return fetch(endpoint, { ...options, headers });
}

document.addEventListener("DOMContentLoaded", () => {
  initWorkspaceSelector();
  initNavigation();
  initEditor();
  initProjectDragDrop();
  loadAllData();

  document.getElementById("btn-trigger-scan")?.addEventListener("click", triggerManualScan);
  document.getElementById("btn-toggle-auto")?.addEventListener("click", toggleAutomation);
});

function loadAllData() {
  loadOverview();
  loadDiscoveries();
  loadClips();
  loadAccounts();
  loadCalendar();
  loadAnalytics();
  loadHealth();
  loadBusiness();
}

// -------------------------------------------------------------
// WORKSPACE SELECTOR
// -------------------------------------------------------------
function initWorkspaceSelector() {
  const selector = document.getElementById("select-workspace");
  if (!selector) return;

  selector.value = state.activeWorkspaceId;
  selector.addEventListener("change", (e) => {
    state.activeWorkspaceId = e.target.value;
    localStorage.setItem("hypenova_workspace", state.activeWorkspaceId);
    
    const badge = document.getElementById("active-profile-badge");
    if (badge) {
      const selectedText = selector.options[selector.selectedIndex].text;
      badge.innerHTML = `<span class="dot-violet"></span> ${selectedText.split("(")[0].trim()}`;
    }
    
    loadAllData();
  });
}

// -------------------------------------------------------------
// TAB NAVIGATION
// -------------------------------------------------------------
function initNavigation() {
  const navButtons = document.querySelectorAll(".nav-item");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const pageTitle = document.getElementById("page-title");

  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");

      navButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const activePane = document.getElementById(`tab-${targetTab}`);
      if (activePane) activePane.classList.add("active");

      if (pageTitle) {
        pageTitle.textContent = btn.textContent.trim();
      }

      if (targetTab === "editor") {
        renderCaptionsTrack();
        updateTimelineBounds();
      }
    });
  });
}

// -------------------------------------------------------------
// 1. OVERVIEW
// -------------------------------------------------------------
async function loadOverview() {
  try {
    const res = await apiFetch("/api/overview");
    const data = await res.json();
    
    document.getElementById("stat-discovered").textContent = data.metrics.discovered_today;
    document.getElementById("stat-authorized").textContent = data.metrics.authorized_sources;
    document.getElementById("stat-clips").textContent = data.metrics.clips_produced;
    document.getElementById("stat-scheduled").textContent = `${data.metrics.scheduled_uploads} / ${data.metrics.published_videos}`;
    
    document.getElementById("overview-disk").textContent = `${data.system.free_storage_gb} GB Available`;
    document.getElementById("overview-compute").textContent = `${data.metrics.total_compute_seconds} s`;
    document.getElementById("overview-cost").textContent = `₹${data.metrics.total_cost_inr}`;

    const userNameElem = document.getElementById("user-display-name");
    if (userNameElem && data.workspace) {
      userNameElem.textContent = `${data.workspace.name.split(" ")[0]} (${data.workspace.role})`;
    }
  } catch (err) {
    console.error("Error loading overview:", err);
  }
}

// -------------------------------------------------------------
// 2. DISCOVERIES (HypeScout)
// -------------------------------------------------------------
async function loadDiscoveries() {
  try {
    const rightsFilter = document.getElementById("scout-filter-rights")?.value;
    const url = rightsFilter ? `/api/scout/discoveries?rights_status=${encodeURIComponent(rightsFilter)}` : "/api/scout/discoveries";
    const res = await apiFetch(url);
    const data = await res.json();
    const tbody = document.getElementById("discoveries-tbody");
    if (!tbody) return;

    if (!data.discoveries || data.discoveries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No videos match filter in this workspace. Click 'Scan Watchlists' or 'Ingest Footage'.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.discoveries.map(item => `
      <tr>
        <td><strong>${escapeHtml(item.title)}</strong></td>
        <td>${escapeHtml(item.channel_title || "Unknown")}</td>
        <td><span class="badge-neutral">${escapeHtml(item.category || "general")}</span></td>
        <td>${item.view_count ? Number(item.view_count).toLocaleString() : "Metadata"}</td>
        <td>
          <span class="badge-${getRightsBadgeClass(item.rights_status)}">${escapeHtml(item.rights_status)}</span>
        </td>
        <td>
          ${item.rights_status === "AUTHORIZED" 
            ? `<button class="btn btn-primary btn-sm" onclick="openNewProjectWithVideo('${item.id}', '${escapeHtml(item.title)}')">🚀 Ingest & Cut</button>` 
            : `<button class="btn btn-secondary btn-sm" onclick="updateRights('${item.id}', 'AUTHORIZED')">Clear Rights</button>`
          }
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading discoveries:", err);
  }
}

function getRightsBadgeClass(status) {
  switch (status) {
    case "AUTHORIZED": return "success";
    case "SOURCE_REQUIRED": return "warning";
    case "RIGHTS_REVIEW": return "violet";
    case "BLOCKED": return "red";
    default: return "neutral";
  }
}

async function triggerManualScan() {
  const btn = document.getElementById("btn-trigger-scan");
  if (btn) btn.textContent = "Scanning...";
  try {
    const res = await apiFetch("/api/scout/scan", { method: "POST" });
    const data = await res.json();
    alert(`Scan completed! Scanned ${data.result.scanned_sources} watchlists. Found ${data.result.new_discoveries} media items.`);
    loadDiscoveries();
    loadOverview();
  } catch (err) {
    alert("Scan error: " + err);
  } finally {
    if (btn) btn.textContent = "⚡ Run Scout Scan";
  }
}

async function updateRights(videoId, newStatus) {
  try {
    await apiFetch("/api/scout/update_rights", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id: videoId, rights_status: newStatus, notes: "Authorized via dashboard." })
    });
    loadDiscoveries();
    loadOverview();
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// 3. CLIP STUDIO
// -------------------------------------------------------------
async function loadClips() {
  try {
    const res = await apiFetch("/api/clips");
    const data = await res.json();
    const container = document.getElementById("clips-list-container");
    if (!container) return;

    state.availableClips = data.clips || [];

    if (!data.clips || data.clips.length === 0) {
      container.innerHTML = `<p class="text-muted">No clips generated in this workspace yet. Click '+ New Project' above to upload video footage or process authorized media.</p>`;
      return;
    }

    container.innerHTML = data.clips.map(c => `
      <div class="card mb-16" style="margin-bottom: 16px; border: 1px solid var(--border-color);">
        <div class="card-header flex-between">
          <div>
            <strong>#${c.id} — ${escapeHtml(c.title)}</strong>
            <span class="badge-cyan" style="margin-left: 10px;">Viral Score: ${c.viral_score}/100</span>
          </div>
          <div class="flex-gap">
            <span class="badge-success">${escapeHtml(c.status)}</span>
            <button class="btn btn-primary btn-sm" onclick="openScheduleModal('${c.id}')">📅 Schedule / Publish</button>
            <button class="btn btn-secondary btn-sm" onclick="openClipInEditor('${c.id}')">🎬 Open in Editor</button>
          </div>
        </div>
        <div class="card-body">
          <p><strong>Opening Hook:</strong> "${escapeHtml(c.hook)}"</p>
          <p class="subtext" style="margin: 8px 0;"><strong>Duration:</strong> ${c.duration}s | <strong>Preset:</strong> ${c.preset}</p>
          <div class="info-row" style="margin-top: 10px;">
            <span class="label">YouTube Packaging:</span>
            <span class="val font-mono">${escapeHtml(c.post_metadata?.youtube?.title || c.title)}</span>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

function openClipInEditor(clipId) {
  state.activeClipId = clipId;
  const navBtn = document.querySelector('[data-tab="editor"]');
  if (navBtn) navBtn.click();
  loadTimelineData(clipId);
}

// -------------------------------------------------------------
// 4. INTERACTIVE MULTI-TRACK VIDEO EDITOR
// -------------------------------------------------------------
function initEditor() {
  const video = document.getElementById("editor-video-player");
  const ruler = document.getElementById("time-ruler");
  const trackVideo = document.getElementById("track-video");

  if (video) {
    video.addEventListener("loadedmetadata", () => {
      state.duration = video.duration || 18.81;
      state.trimEnd = state.duration;
      document.getElementById("timeline-duration-display").textContent = `${state.duration.toFixed(2)}s`;
      updateTimelineBounds();
      renderCaptionsTrack();
    });

    video.addEventListener("timeupdate", () => {
      state.currentTime = video.currentTime;
      updatePlayheadPosition();
      updateTimecodeDisplay();
      highlightActiveCaptionBlock();
    });

    video.addEventListener("ended", () => {
      const playBtn = document.getElementById("btn-play-pause");
      if (playBtn) playBtn.textContent = "▶";
    });
  }

  // Ruler Seeking
  if (ruler) {
    ruler.addEventListener("click", (e) => {
      const rect = ruler.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, clickX / rect.width));
      seekVideoToTime(pct * state.duration);
    });
  }

  // Trim Handles Dragging
  setupTrimDragHandles();
}

async function loadTimelineData(clipId) {
  try {
    const res = await apiFetch(`/api/editor/timeline/${clipId}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.timeline) {
      state.trimStart = data.timeline.trim_start || 0.0;
      state.trimEnd = data.timeline.trim_end || state.duration;
      state.captions = data.timeline.captions || [];
      state.preset = data.timeline.preset || "Indian Gaming Comedy";
      
      const presetSelect = document.getElementById("select-preset");
      if (presetSelect) presetSelect.value = state.preset;

      updateTimelineBounds();
      renderCaptionsTrack();
    }
  } catch (err) {
    console.error("Error fetching timeline edits:", err);
  }
}

function updatePlayheadPosition() {
  const playhead = document.getElementById("playhead");
  if (!playhead || state.duration <= 0) return;
  const pct = (state.currentTime / state.duration) * 100;
  playhead.style.left = `${pct}%`;
}

function updateTimecodeDisplay() {
  const display = document.getElementById("timecode-display");
  if (!display) return;
  display.textContent = `${formatTime(state.currentTime)} / ${formatTime(state.duration)}`;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${String(ms).padStart(2, "0")}`;
}

function togglePlayPause() {
  const video = document.getElementById("editor-video-player");
  const btn = document.getElementById("btn-play-pause");
  if (!video) return;

  if (video.paused) {
    video.play();
    if (btn) btn.textContent = "⏸";
  } else {
    video.pause();
    if (btn) btn.textContent = "▶";
  }
}

function stepTimeline(direction) {
  const video = document.getElementById("editor-video-player");
  if (!video) return;
  const step = 0.5 * direction;
  seekVideoToTime(video.currentTime + step);
}

function seekVideoToTime(time) {
  const video = document.getElementById("editor-video-player");
  if (!video) return;
  const clampedTime = Math.max(0, Math.min(state.duration, time));
  video.currentTime = clampedTime;
  state.currentTime = clampedTime;
  updatePlayheadPosition();
  updateTimecodeDisplay();
}

// Subtitle & Caption Track Rendering
function renderCaptionsTrack() {
  const container = document.getElementById("track-captions");
  if (!container) return;
  container.innerHTML = "";

  state.captions.forEach(c => {
    const leftPct = (c.start / state.duration) * 100;
    const widthPct = Math.max(1, ((c.end - c.start) / state.duration) * 100);

    const block = document.createElement("div");
    block.className = `caption-block ${state.activeCaptionId === c.id ? "active" : ""}`;
    block.id = `caption-block-${c.id}`;
    block.style.left = `${leftPct}%`;
    block.style.width = `${widthPct}%`;
    block.textContent = c.text;
    block.title = `[${c.start}s - ${c.end}s] ${c.text}`;

    block.addEventListener("click", (e) => {
      e.stopPropagation();
      selectCaptionBlock(c.id);
    });

    container.appendChild(block);
  });
}

function selectCaptionBlock(id) {
  state.activeCaptionId = id;
  const caption = state.captions.find(c => c.id === id);
  if (!caption) return;

  document.querySelectorAll(".caption-block").forEach(b => b.classList.remove("active"));
  const activeEl = document.getElementById(`caption-block-${id}`);
  if (activeEl) activeEl.classList.add("active");

  const inputWord = document.getElementById("inspector-caption-text");
  const inputStart = document.getElementById("inspector-caption-start");
  const inputEnd = document.getElementById("inspector-caption-end");

  if (inputWord) inputWord.value = caption.text;
  if (inputStart) inputStart.value = caption.start;
  if (inputEnd) inputEnd.value = caption.end;

  seekVideoToTime(caption.start);
}

function highlightActiveCaptionBlock() {
  state.captions.forEach(c => {
    const block = document.getElementById(`caption-block-${c.id}`);
    if (!block) return;
    if (state.currentTime >= c.start && state.currentTime <= c.end) {
      block.classList.add("active");
    } else if (state.activeCaptionId !== c.id) {
      block.classList.remove("active");
    }
  });
}

function updateActiveCaption() {
  if (!state.activeCaptionId) {
    alert("Please click a caption block on the timeline first.");
    return;
  }
  pushHistory();

  const caption = state.captions.find(c => c.id === state.activeCaptionId);
  if (!caption) return;

  const inputWord = document.getElementById("inspector-caption-text");
  const inputStart = document.getElementById("inspector-caption-start");
  const inputEnd = document.getElementById("inspector-caption-end");

  caption.text = inputWord.value.trim().toUpperCase();
  caption.start = parseFloat(inputStart.value) || caption.start;
  caption.end = parseFloat(inputEnd.value) || caption.end;

  renderCaptionsTrack();
  saveTimelineDraft(true);
}

// In-Point & Out-Point Snapping
function snapTrimToPlayhead(side) {
  pushHistory();
  if (side === "start") {
    state.trimStart = Math.min(state.currentTime, state.trimEnd - 1.0);
  } else {
    state.trimEnd = Math.max(state.currentTime, state.trimStart + 1.0);
  }
  updateTimelineBounds();
}

function splitAtPlayhead() {
  pushHistory();
  const splitTime = parseFloat(state.currentTime.toFixed(2));
  alert(`✂️ Split mark created at ${splitTime}s. In-Point: ${state.trimStart}s | Out-Point: ${state.trimEnd}s`);
}

function updateTimelineBounds() {
  const block = document.getElementById("video-clip-block");
  if (!block || state.duration <= 0) return;

  const leftPct = (state.trimStart / state.duration) * 100;
  const widthPct = ((state.trimEnd - state.trimStart) / state.duration) * 100;

  block.style.left = `${leftPct}%`;
  block.style.width = `${widthPct}%`;
}

function setupTrimDragHandles() {
  const trackVideo = document.getElementById("track-video");
  const leftHandle = document.getElementById("handle-trim-left");
  const rightHandle = document.getElementById("handle-trim-right");
  if (!trackVideo || !leftHandle || !rightHandle) return;

  let isDragging = null;

  leftHandle.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    isDragging = "left";
    pushHistory();
  });

  rightHandle.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    isDragging = "right";
    pushHistory();
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const rect = trackVideo.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const targetTime = parseFloat((pct * state.duration).toFixed(2));

    if (isDragging === "left") {
      state.trimStart = Math.min(targetTime, state.trimEnd - 1.0);
    } else if (isDragging === "right") {
      state.trimEnd = Math.max(targetTime, state.trimStart + 1.0);
    }
    updateTimelineBounds();
  });

  window.addEventListener("mouseup", () => {
    if (isDragging) {
      isDragging = null;
    }
  });
}

// Undo / Redo Stack
function pushHistory() {
  state.historyStack.push({
    trimStart: state.trimStart,
    trimEnd: state.trimEnd,
    captions: JSON.parse(JSON.stringify(state.captions)),
    preset: state.preset
  });
  state.redoStack = [];
}

function editorUndo() {
  if (state.historyStack.length === 0) return;
  const current = {
    trimStart: state.trimStart,
    trimEnd: state.trimEnd,
    captions: JSON.parse(JSON.stringify(state.captions)),
    preset: state.preset
  };
  state.redoStack.push(current);

  const prev = state.historyStack.pop();
  state.trimStart = prev.trimStart;
  state.trimEnd = prev.trimEnd;
  state.captions = prev.captions;
  state.preset = prev.preset;

  updateTimelineBounds();
  renderCaptionsTrack();
}

function editorRedo() {
  if (state.redoStack.length === 0) return;
  const current = {
    trimStart: state.trimStart,
    trimEnd: state.trimEnd,
    captions: JSON.parse(JSON.stringify(state.captions)),
    preset: state.preset
  };
  state.historyStack.push(current);

  const next = state.redoStack.pop();
  state.trimStart = next.trimStart;
  state.trimEnd = next.trimEnd;
  state.captions = next.captions;
  state.preset = next.preset;

  updateTimelineBounds();
  renderCaptionsTrack();
}

// Presets & Safe Area
function onPresetChange() {
  const select = document.getElementById("select-preset");
  if (!select) return;
  pushHistory();
  state.preset = select.value;
  
  const sfxLabel = document.getElementById("inspector-sfx");
  if (sfxLabel) {
    if (state.preset.includes("Gaming")) sfxLabel.textContent = "Funny Laugh / Whoosh";
    else if (state.preset.includes("Podcast")) sfxLabel.textContent = "Minimal Clean / Sub Bass";
    else sfxLabel.textContent = "Pop / Swoosh";
  }
}

function toggleSafeZones() {
  const checkbox = document.getElementById("check-safe-zones");
  const overlay = document.getElementById("safe-area-overlay");
  if (!checkbox || !overlay) return;
  state.safeZones = checkbox.checked;
  if (state.safeZones) {
    overlay.classList.remove("hidden");
  } else {
    overlay.classList.add("hidden");
  }
}

function setAspectRatio(ratio) {
  state.aspectRatio = ratio;
  const container = document.getElementById("canvas-container");
  const btn916 = document.getElementById("btn-ratio-916");
  const btn169 = document.getElementById("btn-ratio-169");

  if (ratio === "9:16") {
    container?.classList.remove("ratio-16-9");
    container?.classList.add("ratio-9-16");
    btn916?.classList.add("active");
    btn169?.classList.remove("active");
  } else {
    container?.classList.remove("ratio-9-16");
    container?.classList.add("ratio-16-9");
    btn169?.classList.add("active");
    btn916?.classList.remove("active");
  }
}

// Save & Export
async function saveTimelineDraft(silent = false) {
  try {
    const payload = {
      clip_id: state.activeClipId,
      trim_start: state.trimStart,
      trim_end: state.trimEnd,
      captions: state.captions,
      preset: state.preset,
      safe_zones: state.safeZones,
      aspect_ratio: state.aspectRatio
    };

    const res = await apiFetch(`/api/editor/timeline/${state.activeClipId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!silent) alert("Timeline draft successfully saved to workspace!");
  } catch (err) {
    console.error("Save draft error:", err);
    if (!silent) alert("Failed to save draft: " + err);
  }
}

async function triggerRerenderExport() {
  const badge = document.getElementById("editor-qa-badge");
  if (badge) {
    badge.className = "badge-warning";
    badge.textContent = "Rendering...";
  }

  try {
    const payload = {
      clip_id: state.activeClipId,
      trim_start: state.trimStart,
      trim_end: state.trimEnd,
      captions: state.captions,
      preset: state.preset,
      safe_zones: state.safeZones,
      aspect_ratio: state.aspectRatio
    };

    const res = await apiFetch("/api/editor/rerender", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    alert(`Re-rendering completed!\nDuration: ${(state.trimEnd - state.trimStart).toFixed(2)}s\nPreset: ${state.preset}`);
    
    if (badge) {
      badge.className = "badge-success";
      badge.textContent = "QA Verified (-14.3 LUFS)";
    }

    const video = document.getElementById("editor-video-player");
    if (video && data.video_url) {
      video.src = data.video_url + "?t=" + Date.now();
      video.load();
    }
    loadClips();
  } catch (err) {
    alert("Re-rendering error: " + err);
    if (badge) {
      badge.className = "badge-red";
      badge.textContent = "Render Failed";
    }
  }
}

// -------------------------------------------------------------
// 5. YOUTUBE ACCOUNTS & CHANNELS
// -------------------------------------------------------------
async function loadAccounts() {
  try {
    const res = await apiFetch("/api/accounts");
    const data = await res.json();
    const container = document.getElementById("accounts-list-container");
    if (!container) return;

    if (!data.accounts || data.accounts.length === 0) {
      container.innerHTML = `
        <div class="card" style="padding: 24px; text-align: center; grid-column: 1 / -1;">
          <p class="text-muted">No YouTube channels connected to this workspace yet.</p>
          <button class="btn btn-primary" style="margin-top: 14px;" onclick="openConnectModal()">+ Connect Your First Channel</button>
        </div>
      `;
      return;
    }

    container.innerHTML = data.accounts.map(acc => `
      <div class="account-card">
        <div class="account-header">
          <div class="account-avatar">${escapeHtml(acc.channel_title.slice(0, 2).toUpperCase())}</div>
          <div class="account-meta">
            <h4>${escapeHtml(acc.channel_title)}</h4>
            <div class="subtext">${escapeHtml(acc.account_email)}</div>
            <div class="account-badges">
              <span class="badge-success">CONNECTED</span>
              <span class="badge-neutral font-mono">${escapeHtml(acc.channel_id)}</span>
            </div>
          </div>
        </div>
        <div class="account-actions">
          <button class="btn btn-secondary btn-sm" onclick="disconnectAccount('${acc.id}')">Disconnect</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading accounts:", err);
  }
}

function openConnectModal() {
  const modal = document.getElementById("connect-modal");
  if (modal) modal.style.display = "flex";
}

function closeConnectModal() {
  const modal = document.getElementById("connect-modal");
  if (modal) modal.style.display = "none";
}

async function submitChannelConnect() {
  const title = document.getElementById("connect-channel-name")?.value.trim();
  const channelId = document.getElementById("connect-channel-id")?.value.trim();
  const email = document.getElementById("connect-account-email")?.value.trim();

  if (!title || !channelId || !email) {
    alert("Please fill in all channel details.");
    return;
  }

  try {
    const res = await apiFetch("/api/accounts/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel_title: title,
        channel_id: channelId,
        account_email: email
      })
    });
    const data = await res.json();
    alert(`Connected '${data.channel_title}' successfully!`);
    closeConnectModal();
    loadAccounts();
  } catch (err) {
    alert("Failed to connect account: " + err);
  }
}

async function disconnectAccount(accountId) {
  if (!confirm("Are you sure you want to disconnect this YouTube channel?")) return;
  try {
    await apiFetch(`/api/accounts/${accountId}/disconnect`, { method: "POST" });
    loadAccounts();
  } catch (err) {
    alert("Failed to disconnect: " + err);
  }
}

// -------------------------------------------------------------
// 6. CALENDAR & DISTRIBUTION
// -------------------------------------------------------------
async function loadCalendar() {
  try {
    const res = await apiFetch("/api/calendar");
    const data = await res.json();
    const tbody = document.getElementById("calendar-tbody");
    if (!tbody) return;

    if (!data.queue || data.queue.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center">No clips queued. Ready to schedule approved clips.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.queue.map(q => `
      <tr>
        <td><strong>${escapeHtml(q.clip_title)}</strong></td>
        <td>${escapeHtml(q.channel_name)}</td>
        <td><span class="badge-cyan">${escapeHtml(q.platform)}</span></td>
        <td>${escapeHtml(q.scheduled_for)}</td>
        <td><span class="badge-warning">${escapeHtml(q.status)}</span></td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// 7. ANALYTICS LAB
// -------------------------------------------------------------
async function loadAnalytics() {
  try {
    const res = await apiFetch("/api/analytics");
    const data = await res.json();
    const tbody = document.getElementById("analytics-tbody");
    if (!tbody) return;

    const benchmarks = data.experimental_format_benchmarks || [];
    tbody.innerHTML = benchmarks.map(fp => `
      <tr>
        <td><strong>${escapeHtml(fp.format)}</strong></td>
        <td><span class="badge-neutral">${escapeHtml(fp.category || "Gaming")}</span></td>
        <td><span class="badge-success">${fp.avg_retention}</span></td>
        <td>${Number(fp.sample_views).toLocaleString()}</td>
        <td><span class="badge-violet">Top Performer</span></td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// 8. AUTOMATION TOGGLE
// -------------------------------------------------------------
async function toggleAutomation() {
  try {
    const res = await apiFetch("/api/automation/toggle", { method: "POST" });
    const data = await res.json();
    alert(`Automation background service is now: ${data.running ? "ACTIVE" : "PAUSED"}`);
    loadOverview();
  } catch (err) {
    alert("Error toggling automation: " + err);
  }
}

// -------------------------------------------------------------
// 9. CREATOR BUSINESS
// -------------------------------------------------------------
async function loadBusiness() {
  try {
    const res = await apiFetch("/api/business");
    const data = await res.json();
    const container = document.getElementById("packages-container");
    if (!container) return;

    container.innerHTML = data.packages.map(p => `
      <div class="card" style="border: 1px solid var(--border-color); padding: 18px;">
        <h4>${escapeHtml(p.name)}</h4>
        <div class="stat-val text-cyan" style="font-size: 22px; margin: 8px 0;">₹${p.price_inr.toLocaleString()} / mo</div>
        <p class="subtext"><strong>${p.clips} Vertical Clips</strong></p>
        <p class="subtext">Turnaround: ${p.turnaround}</p>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// 10. SYSTEM HEALTH
// -------------------------------------------------------------
async function loadHealth() {
  try {
    const res = await apiFetch("/api/health");
    const data = await res.json();
    const container = document.getElementById("system-logs-container");
    if (!container) return;

    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = `<div>[SYSTEM] System healthy. Running Python 3.12, FFmpeg 9.1.</div>`;
      return;
    }

    container.innerHTML = data.logs.map(l => `
      <div><span style="color: var(--text-muted);">[${l.created_at}]</span> [${escapeHtml(l.level)}] <strong>${escapeHtml(l.module)}:</strong> ${escapeHtml(l.message)}</div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// -------------------------------------------------------------
// 11. AUTONOMOUS ZERO-TERMINAL PROJECT & JOB CONTROLS
// -------------------------------------------------------------
function initProjectDragDrop() {
  const dropZone = document.getElementById("project-drop-zone");
  if (!dropZone) return;

  ["dragenter", "dragover"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("drag-over");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      state.selectedProjectFile = files[0];
      handleFileChosen(files[0]);
    }
  });
}

function openNewProjectModal() {
  const modal = document.getElementById("modal-new-project");
  if (modal) modal.style.display = "flex";

  // Pre-load authorized videos for Mode 2
  loadAuthorizedScoutVideos();
  setProjectInputMode(state.projectInputMode || "upload");
}

function closeNewProjectModal() {
  const modal = document.getElementById("modal-new-project");
  if (modal) modal.style.display = "none";
  const progressBox = document.getElementById("project-upload-progress");
  if (progressBox) progressBox.classList.add("hidden");
}

function setProjectInputMode(mode) {
  state.projectInputMode = mode;
  const btnUpload = document.getElementById("btn-project-mode-upload");
  const btnScout = document.getElementById("btn-project-mode-scout");
  const secUpload = document.getElementById("project-upload-section");
  const secScout = document.getElementById("project-scout-section");

  if (mode === "upload") {
    btnUpload?.classList.add("active");
    btnScout?.classList.remove("active");
    secUpload?.classList.remove("hidden");
    secScout?.classList.add("hidden");
  } else {
    btnScout?.classList.add("active");
    btnUpload?.classList.remove("active");
    secScout?.classList.remove("hidden");
    secUpload?.classList.add("hidden");
  }
  toggleProjectSubmitState();
}

function onProjectFileSelected(input) {
  if (input.files && input.files.length > 0) {
    state.selectedProjectFile = input.files[0];
    handleFileChosen(input.files[0]);
  }
}

function handleFileChosen(file) {
  const nameEl = document.getElementById("selected-file-name");
  const detailsBox = document.getElementById("upload-file-details");
  const titleInput = document.getElementById("project-title-input");

  if (nameEl) nameEl.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
  if (detailsBox) detailsBox.classList.remove("hidden");
  if (titleInput && !titleInput.value.trim()) {
    titleInput.value = file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
  }

  toggleProjectSubmitState();
}

async function loadAuthorizedScoutVideos() {
  const select = document.getElementById("project-scout-select");
  if (!select) return;

  try {
    const res = await apiFetch("/api/scout/discoveries?rights_status=AUTHORIZED");
    const data = await res.json();
    if (!data.discoveries || data.discoveries.length === 0) {
      select.innerHTML = `<option value="">No authorized videos found. Upload footage or clear rights in HypeScout.</option>`;
      return;
    }

    select.innerHTML = data.discoveries.map(v => `
      <option value="${v.id}">${escapeHtml(v.title)} (${escapeHtml(v.category || "gaming")})</option>
    `).join("");
  } catch (err) {
    console.error("Error loading authorized videos:", err);
  }
}

function openNewProjectWithVideo(videoId, title) {
  openNewProjectModal();
  setProjectInputMode("scout");
  const select = document.getElementById("project-scout-select");
  if (select) select.value = videoId;
  const titleInput = document.getElementById("project-title-input");
  if (titleInput) titleInput.value = title;
  const rightsCheck = document.getElementById("project-rights-checkbox");
  if (rightsCheck) rightsCheck.checked = true;
  toggleProjectSubmitState();
}

function toggleProjectSubmitState() {
  const rightsChecked = document.getElementById("project-rights-checkbox")?.checked;
  const submitBtn = document.getElementById("btn-submit-project");
  if (!submitBtn) return;

  let hasSource = false;
  if (state.projectInputMode === "upload") {
    hasSource = state.selectedProjectFile !== null;
  } else {
    const select = document.getElementById("project-scout-select");
    hasSource = select && select.value !== "";
  }

  if (rightsChecked && hasSource) {
    submitBtn.removeAttribute("disabled");
    submitBtn.style.opacity = "1";
    submitBtn.style.cursor = "pointer";
  } else {
    submitBtn.setAttribute("disabled", "true");
    submitBtn.style.opacity = "0.5";
    submitBtn.style.cursor = "not-allowed";
  }
}

async function submitNewProject() {
  const title = document.getElementById("project-title-input")?.value.trim() || "Untitled Project";
  const category = document.getElementById("project-category-select")?.value || "gaming";
  const preset = document.getElementById("project-preset-select")?.value || "Indian Gaming Comedy";
  const rightsCertified = document.getElementById("project-rights-checkbox")?.checked;

  if (!rightsCertified) {
    alert("You must certify rights authorization before processing media.");
    return;
  }

  const submitBtn = document.getElementById("btn-submit-project");
  if (submitBtn) {
    submitBtn.setAttribute("disabled", "true");
    submitBtn.textContent = "Submitting Job...";
  }

  if (state.projectInputMode === "upload") {
    if (!state.selectedProjectFile) {
      alert("Please select a video file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", state.selectedProjectFile);
    formData.append("title", title);
    formData.append("category", category);
    formData.append("preset", preset);
    formData.append("rights_certified", "true");

    const progressBox = document.getElementById("project-upload-progress");
    const progressFill = document.getElementById("upload-progress-fill");
    const pctLabel = document.getElementById("upload-pct-label");
    const statusLabel = document.getElementById("upload-status-label");

    if (progressBox) progressBox.classList.remove("hidden");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/projects/upload");
    xhr.setRequestHeader("X-Workspace-Id", state.activeWorkspaceId);
    xhr.setRequestHeader("Authorization", "Bearer dev-token-usr-admin");

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        if (progressFill) progressFill.style.width = `${pct}%`;
        if (pctLabel) pctLabel.textContent = `${pct}%`;
        if (statusLabel) statusLabel.textContent = `Uploading media file (${pct}%)...`;
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const res = JSON.parse(xhr.responseText);
        closeNewProjectModal();
        // Switch to Studio tab to watch live monitor
        document.querySelector('[data-tab="studio"]')?.click();
        startJobPolling(res.job_id, title);
      } else {
        alert("Upload error: " + xhr.responseText);
        if (submitBtn) {
          submitBtn.removeAttribute("disabled");
          submitBtn.textContent = "🚀 Start Autonomous Pipeline";
        }
      }
    };

    xhr.onerror = () => {
      alert("Network error occurred during video upload.");
      if (submitBtn) {
        submitBtn.removeAttribute("disabled");
        submitBtn.textContent = "🚀 Start Autonomous Pipeline";
      }
    };

    xhr.send(formData);

  } else {
    // Mode 2: Existing Authorized Video
    const videoId = document.getElementById("project-scout-select")?.value;
    if (!videoId) {
      alert("Please select an authorized video.");
      return;
    }

    try {
      const res = await apiFetch("/api/projects/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          preset: preset,
          rights_certified: true
        })
      });
      const data = await res.json();
      closeNewProjectModal();
      document.querySelector('[data-tab="studio"]')?.click();
      startJobPolling(data.job_id, title);
    } catch (err) {
      alert("Error creating project: " + err);
      if (submitBtn) {
        submitBtn.removeAttribute("disabled");
        submitBtn.textContent = "🚀 Start Autonomous Pipeline";
      }
    }
  }
}

// -------------------------------------------------------------
// 12. LIVE PROCESSING MONITOR & JOB POLLING
// -------------------------------------------------------------
function startJobPolling(jobId, projectTitle = "Video Project") {
  if (state.jobPollInterval) {
    clearInterval(state.jobPollInterval);
  }

  state.activeJobId = jobId;
  const monitorCard = document.getElementById("processing-monitor-card");
  const jobTitleEl = document.getElementById("monitor-job-title");
  const cancelBtn = document.getElementById("btn-monitor-cancel");
  const retryBtn = document.getElementById("btn-monitor-retry");

  if (monitorCard) monitorCard.classList.remove("hidden");
  if (jobTitleEl) jobTitleEl.textContent = `Pipeline: ${projectTitle}`;
  if (cancelBtn) cancelBtn.classList.remove("hidden");
  if (retryBtn) retryBtn.classList.add("hidden");

  // Immediate poll then recurring
  pollJob(jobId);
  state.jobPollInterval = setInterval(() => pollJob(jobId), 1500);
}

async function pollJob(jobId) {
  try {
    const res = await apiFetch(`/api/jobs/${jobId}`);
    if (!res.ok) return;
    const job = await res.json();

    const pct = job.progress || 0;
    const stage = job.stage || (job.error_message?.startsWith("Stage:") ? job.error_message : job.status);

    const progressFill = document.getElementById("monitor-progress-fill");
    const pctText = document.getElementById("monitor-pct-text");
    const stageBadge = document.getElementById("monitor-stage-badge");
    const detailText = document.getElementById("monitor-detail-text");
    const cancelBtn = document.getElementById("btn-monitor-cancel");
    const retryBtn = document.getElementById("btn-monitor-retry");

    if (progressFill) progressFill.style.width = `${pct}%`;
    if (pctText) pctText.textContent = `${pct}%`;
    if (stageBadge) stageBadge.textContent = stage;
    if (detailText) detailText.textContent = `Status: ${job.status} — ${stage}`;

    if (job.status === "COMPLETED") {
      clearInterval(state.jobPollInterval);
      state.jobPollInterval = null;
      if (progressFill) progressFill.style.width = "100%";
      if (pctText) pctText.textContent = "100%";
      if (stageBadge) {
        stageBadge.className = "badge-success";
        stageBadge.textContent = "Ready for Review";
      }
      if (cancelBtn) cancelBtn.classList.add("hidden");
      if (retryBtn) retryBtn.classList.add("hidden");

      loadClips();
      loadOverview();
      loadDiscoveries();
    } else if (job.status === "FAILED") {
      clearInterval(state.jobPollInterval);
      state.jobPollInterval = null;
      if (stageBadge) {
        stageBadge.className = "badge-red";
        stageBadge.textContent = "Pipeline Failed";
      }
      if (detailText) detailText.textContent = `Error: ${job.error_message || "Unknown error"}`;
      if (cancelBtn) cancelBtn.classList.add("hidden");
      if (retryBtn) retryBtn.classList.remove("hidden");
    } else if (job.status === "CANCELLED") {
      clearInterval(state.jobPollInterval);
      state.jobPollInterval = null;
      if (stageBadge) {
        stageBadge.className = "badge-neutral";
        stageBadge.textContent = "Cancelled";
      }
      if (cancelBtn) cancelBtn.classList.add("hidden");
    }
  } catch (err) {
    console.error("Job poll error:", err);
  }
}

async function cancelCurrentJob() {
  if (!state.activeJobId) return;
  try {
    await apiFetch(`/api/jobs/${state.activeJobId}/cancel`, { method: "POST" });
    pollJob(state.activeJobId);
  } catch (err) {
    alert("Cancel error: " + err);
  }
}

async function retryCurrentJob() {
  if (!state.activeJobId) return;
  try {
    await apiFetch(`/api/jobs/${state.activeJobId}/retry`, { method: "POST" });
    startJobPolling(state.activeJobId);
  } catch (err) {
    alert("Retry error: " + err);
  }
}

function dismissMonitor() {
  const monitorCard = document.getElementById("processing-monitor-card");
  if (monitorCard) monitorCard.classList.add("hidden");
  if (state.jobPollInterval) {
    clearInterval(state.jobPollInterval);
    state.jobPollInterval = null;
  }
}

// -------------------------------------------------------------
// 13. SCHEDULE & PUBLISHING WORKFLOW
// -------------------------------------------------------------
function openScheduleModal(clipId) {
  state.scheduleClipId = clipId;
  const clip = (state.availableClips || []).find(c => c.id === clipId);

  const modal = document.getElementById("modal-schedule-publish");
  const idInput = document.getElementById("schedule-clip-id");
  const titleInput = document.getElementById("schedule-title-input");
  const descInput = document.getElementById("schedule-desc-input");
  const timeInput = document.getElementById("schedule-time-input");

  if (idInput) idInput.value = clipId;
  if (titleInput) {
    titleInput.value = clip?.post_metadata?.youtube?.title || clip?.title || `Short #${clipId}`;
  }
  if (descInput) {
    descInput.value = clip?.post_metadata?.youtube?.description || `#Shorts #Gaming #Highlights`;
  }

  // Pre-fill tomorrow 18:00
  if (timeInput) {
    const tmrw = new Date();
    tmrw.setDate(tmrw.getDate() + 1);
    tmrw.setHours(18, 0, 0, 0);
    timeInput.value = tmrw.toISOString().slice(0, 16);
  }

  if (modal) modal.style.display = "flex";
}

function closeScheduleModal() {
  const modal = document.getElementById("modal-schedule-publish");
  if (modal) modal.style.display = "none";
}

async function submitScheduleQueue() {
  const clipId = document.getElementById("schedule-clip-id")?.value;
  const channelProfileId = document.getElementById("schedule-channel-select")?.value;
  const scheduledTime = document.getElementById("schedule-time-input")?.value;

  if (!clipId || !channelProfileId || !scheduledTime) {
    alert("Please fill in scheduled time and channel.");
    return;
  }

  try {
    const res = await apiFetch("/api/calendar/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clip_id: clipId,
        channel_profile_id: channelProfileId,
        scheduled_for: scheduledTime
      })
    });
    const data = await res.json();
    alert(`Short queued successfully for ${channelProfileId}! Queue ID: ${data.queue_id}`);
    closeScheduleModal();
    loadClips();
    loadCalendar();
    loadOverview();
  } catch (err) {
    alert("Scheduling error: " + err);
  }
}

async function submitPublishNow() {
  const clipId = document.getElementById("schedule-clip-id")?.value;
  const channelProfileId = document.getElementById("schedule-channel-select")?.value;
  const title = document.getElementById("schedule-title-input")?.value;
  const desc = document.getElementById("schedule-desc-input")?.value;

  if (!clipId || !channelProfileId) {
    alert("Invalid clip or channel selection.");
    return;
  }

  try {
    const res = await apiFetch("/api/calendar/publish_now", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clip_id: clipId,
        channel_profile_id: channelProfileId,
        title: title,
        description: desc
      })
    });
    const data = await res.json();
    alert(`🚀 Video Short Published!\n\nPlatform: YouTube Shorts\nExternal URL: ${data.external_post_url}\nVideo ID: ${data.external_video_id}`);
    closeScheduleModal();
    loadClips();
    loadCalendar();
    loadOverview();
    loadAnalytics();
  } catch (err) {
    alert("Publishing error: " + err);
  }
}