(function () {
  "use strict";

  // ── Configure marked.js ────────────────────────────────────────────────
  if (typeof marked !== "undefined") {
    marked.setOptions({ breaks: true, gfm: true });
  }

  // ── DOM refs ───────────────────────────────────────────────────────────
  const loadingEl        = document.getElementById("loading");
  const onboardingScreen = document.getElementById("onboarding-screen");
  const goalsScreen      = document.getElementById("goals-screen");
  const chatScreen       = document.getElementById("chat-screen");

  // Onboarding
  const uploadForm       = document.getElementById("upload-form");
  const resumeZone       = document.getElementById("resume-zone");
  const resumeInput      = document.getElementById("resumes-input");
  const resumeList       = document.getElementById("resume-list");
  const linkedinZone     = document.getElementById("linkedin-zone");
  const linkedinInput    = document.getElementById("linkedin-input");
  const linkedinList     = document.getElementById("linkedin-list");
  const uploadError      = document.getElementById("upload-error");
  const uploadBtn        = document.getElementById("upload-btn");
  const uploadBtnText    = document.getElementById("upload-btn-text");
  const uploadBtnSpinner = document.getElementById("upload-btn-spinner");

  // Goals (after first profile creation)
  const goalsForm     = document.getElementById("goals-form");
  const goalsTargetRole = document.getElementById("goals-target-role");
  const goalsFocus    = document.getElementById("goals-focus");

  // Chat
  const profileSelect    = document.getElementById("profile-select");
  const targetRoleInput  = document.getElementById("target-role");
  const newChatBtn       = document.getElementById("new-chat-btn");
  const progressBtn      = document.getElementById("progress-btn");
  const messagesEl       = document.getElementById("messages");
  const emptyState       = document.getElementById("empty-state");
  const toolStatusEl     = document.getElementById("tool-status");
  const toolStatusText   = document.getElementById("tool-status-text");
  const messageInput     = document.getElementById("message-input");
  const sendBtn          = document.getElementById("send-btn");
  const chatFileInput    = document.getElementById("chat-file-input");
  const attachBtn        = document.getElementById("attach-btn");
  const chatAttachedEl   = document.getElementById("chat-attached");

  // Progress panel
  const progressBackdrop   = document.getElementById("progress-backdrop");
  const progressPanel      = document.getElementById("progress-panel");
  const closeProgressBtn   = document.getElementById("close-progress-btn");
  const refreshProgressBtn = document.getElementById("refresh-progress-btn");
  const suggestedCard      = document.getElementById("suggested-next-card");
  const suggestedLabel     = document.getElementById("suggested-label");
  const suggestedEmpty     = document.getElementById("suggested-empty");
  const weakList           = document.getElementById("weak-topics-list");
  const strongList         = document.getElementById("strong-topics-list");

  // ── State ──────────────────────────────────────────────────────────────
  const API = "";
  let profileStatus    = { exists: false, default_profile_id: null, profiles: [] };
  let sessionId        = sessionStorage.getItem("studia_session_id") || ("web-" + Math.random().toString(36).slice(2));
  let selectedProfileId = sessionStorage.getItem("studia_profile_id") || "";
  let isStreaming      = false;

  // Per-upload-zone file lists (since FileList is read-only we track arrays)
  let resumeFiles      = [];
  let linkedinFile     = null;

  // Chat input: attached files for current message
  let chatAttachedFiles = [];

  sessionStorage.setItem("studia_session_id", sessionId);

  // ── Utility helpers ────────────────────────────────────────────────────
  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }

  function showScreen(id) {
    loadingEl.style.display = "none";
    [onboardingScreen, goalsScreen, chatScreen].forEach(function (s) {
      if (s) s.classList.remove("active");
    });
    const target = document.getElementById(id);
    if (target) target.classList.add("active");
  }

  function renderMarkdown(text) {
    if (typeof marked === "undefined") return escapeHtml(text).replace(/\n/g, "<br>");
    const raw = marked.parse(text);
    if (typeof DOMPurify !== "undefined") return DOMPurify.sanitize(raw);
    return raw;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function removeEmptyState() {
    if (emptyState && emptyState.parentNode === messagesEl) {
      messagesEl.removeChild(emptyState);
    }
  }

  // ── Upload zones ───────────────────────────────────────────────────────
  function renderFilePills(container, files, onRemove) {
    container.innerHTML = "";
    files.forEach(function (file, idx) {
      const pill = document.createElement("div");
      pill.className = "file-pill";
      pill.innerHTML =
        "<span class=\"file-pill-name\" title=\"" + escapeHtml(file.name) + "\">" + escapeHtml(file.name) + "</span>" +
        "<button type=\"button\" class=\"file-pill-remove\" aria-label=\"Remove " + escapeHtml(file.name) + "\">✕</button>";
      pill.querySelector(".file-pill-remove").addEventListener("click", function (e) {
        e.stopPropagation();
        onRemove(idx);
      });
      container.appendChild(pill);
    });
  }

  function setupUploadZone(zone, input, getFiles, setFiles, listEl, multi) {
    // The input is an opacity:0 overlay over the zone — clicks go straight to it.
    // Keydown on the zone div triggers it for keyboard users.
    zone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
    });

    input.addEventListener("change", function () {
      if (!input.files || input.files.length === 0) return;
      if (multi) {
        const newFiles = Array.from(input.files);
        setFiles(getFiles().concat(newFiles));
      } else {
        setFiles([input.files[0]]);
      }
      input.value = "";
      refreshZone();
    });

    function refreshZone() {
      const current = getFiles();
      if (current.length > 0) {
        zone.classList.add("has-files");
      } else {
        zone.classList.remove("has-files");
      }
      renderFilePills(listEl, current, function (idx) {
        const arr = getFiles().slice();
        arr.splice(idx, 1);
        setFiles(arr);
        refreshZone();
      });
    }
  }

  setupUploadZone(
    resumeZone, resumeInput,
    function () { return resumeFiles; },
    function (arr) { resumeFiles = arr; },
    resumeList,
    true
  );

  setupUploadZone(
    linkedinZone, linkedinInput,
    function () { return linkedinFile ? [linkedinFile] : []; },
    function (arr) { linkedinFile = arr.length > 0 ? arr[0] : null; },
    linkedinList,
    false
  );

  // ── Messages ───────────────────────────────────────────────────────────
  function appendMessage(role, content, animate) {
    removeEmptyState();
    if (animate === undefined) animate = true;

    const row = document.createElement("div");
    row.className = "msg-row " + role;
    if (!animate) row.style.animation = "none";

    const bubble = document.createElement("div");
    bubble.className = "bubble " + role;

    if (role === "user") {
      bubble.textContent = content;
    } else {
      bubble.innerHTML = renderMarkdown(content);
    }

    if (role === "assistant") {
      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = "S";
      row.appendChild(avatar);
    }

    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
    return { row, bubble };
  }

  function addTypingIndicator() {
    removeEmptyState();
    const row = document.createElement("div");
    row.className = "msg-row assistant";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "S";

    const bubble = document.createElement("div");
    bubble.className = "bubble assistant";
    bubble.innerHTML = "<div class=\"typing-dots\"><span></span><span></span><span></span></div>";

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
    return row;
  }

  function removeTypingIndicator(el) {
    if (el && el.parentNode === messagesEl) {
      messagesEl.removeChild(el);
    }
  }

  // ── Tool status bar ────────────────────────────────────────────────────
  function showToolStatus(label) {
    toolStatusText.textContent = label || "Working…";
    show(toolStatusEl);
  }

  function hideToolStatus() {
    hide(toolStatusEl);
  }

  // Chat-first: welcome message when no profile and empty history (not persisted)
  const WELCOME_NO_PROFILE = "I'm your interview prep coach. To get started, upload your resume or CV (one or more files) using the attachment button below, or tell me and I'll ask you a few questions to build your profile. Once your profile is set, we can start practicing.";

  // ── Profile screen setup ───────────────────────────────────────────────
  function renderScreens() {
    // Chat-first: always show chat screen; no onboarding gate
    showScreen("chat-screen");

    if (profileStatus.exists) {
      const defaultId = selectedProfileId ||
        profileStatus.default_profile_id ||
        (profileStatus.profiles[0] && profileStatus.profiles[0].id) || "";
      selectedProfileId = defaultId;
      sessionStorage.setItem("studia_profile_id", selectedProfileId);

      // Populate profile dropdown
      profileSelect.innerHTML = "";
      profileStatus.profiles.forEach(function (p) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.label || p.id;
        if (p.id === selectedProfileId) opt.selected = true;
        profileSelect.appendChild(opt);
      });
    } else {
      profileSelect.innerHTML = "";
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No profile yet";
      opt.selected = true;
      profileSelect.appendChild(opt);
    }

    loadHistory();
  }

  profileSelect.addEventListener("change", function () {
    selectedProfileId = profileSelect.value;
    sessionStorage.setItem("studia_profile_id", selectedProfileId);
  });

  // ── Goals step (after first profile creation) ────────────────────────────
  goalsForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const targetRole = (goalsTargetRole && goalsTargetRole.value || "").trim();
    const focus = (goalsFocus && goalsFocus.value || "").trim();
    if (targetRole) sessionStorage.setItem("studia_target_role", targetRole);
    showScreen("chat-screen");
    if (profileStatus.profiles && profileStatus.profiles.length) {
      profileSelect.innerHTML = "";
      profileStatus.profiles.forEach(function (p) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.label || p.id;
        if (p.id === selectedProfileId) opt.selected = true;
        profileSelect.appendChild(opt);
      });
    }
    if (targetRoleInput) targetRoleInput.value = targetRole;
    if (focus && messageInput) {
      messageInput.value = focus;
      messageInput.style.height = "auto";
      messageInput.style.height = messageInput.scrollHeight + "px";
    }
    loadHistory();
  });

  // ── Session history ────────────────────────────────────────────────────
  async function loadHistory() {
    try {
      const r = await fetch(API + "/session/history?session_id=" + encodeURIComponent(sessionId));
      if (!r.ok) return;
      const history = await r.json();
      messagesEl.innerHTML = "";
      if (history.length === 0) {
        if (!profileStatus.exists) {
          appendMessage("assistant", WELCOME_NO_PROFILE, false);
          return;
        }
        messagesEl.appendChild(emptyState);
        show(emptyState);
        return;
      }
      history.forEach(function (h) {
        appendMessage(h.role, h.content, false);
      });
    } catch (_) {
      messagesEl.innerHTML = "";
      if (!profileStatus.exists) {
        appendMessage("assistant", WELCOME_NO_PROFILE, false);
        return;
      }
      messagesEl.appendChild(emptyState);
      show(emptyState);
    }
  }

  // ── Upload form ────────────────────────────────────────────────────────
  uploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    hide(uploadError);

    if (resumeFiles.length === 0 && !linkedinFile) {
      uploadError.textContent = "Please upload at least one resume or a LinkedIn ZIP.";
      show(uploadError);
      return;
    }

    const labelVal = (document.getElementById("profile-label").value || "").trim();

    uploadBtn.disabled = true;
    hide(uploadBtnText);
    show(uploadBtnSpinner);

    const formData = new FormData();
    if (labelVal) formData.append("label", labelVal);
    resumeFiles.forEach(function (f) { formData.append("resumes", f); });
    if (linkedinFile) formData.append("linkedin", linkedinFile);

    try {
      const r = await fetch(API + "/profile/from-uploads", { method: "POST", body: formData });
      const data = await r.json().catch(function () { return {}; });
      if (!r.ok) {
        uploadError.textContent = data.detail || data.message || "Upload failed. Please try again.";
        show(uploadError);
        uploadBtn.disabled = false;
        show(uploadBtnText);
        hide(uploadBtnSpinner);
        return;
      }
      profileStatus = await fetchProfileStatus();
      if (data.profile_id) {
        selectedProfileId = data.profile_id;
        sessionStorage.setItem("studia_profile_id", selectedProfileId);
      }
      showScreen("goals-screen");
    } catch (err) {
      uploadError.textContent = err.message || "Network error. Is the backend running?";
      show(uploadError);
      uploadBtn.disabled = false;
      show(uploadBtnText);
      hide(uploadBtnSpinner);
    }
  });

  // ── Chat form ──────────────────────────────────────────────────────────
  // Auto-grow textarea
  messageInput.addEventListener("input", function () {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
  });

  // Send on Enter (Shift+Enter = newline)
  messageInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitChat();
    }
  });

  sendBtn.addEventListener("click", function () {
    submitChat();
  });

  // Attach files in chat
  if (attachBtn && chatFileInput) {
    attachBtn.addEventListener("click", function () { chatFileInput.click(); });
    chatFileInput.addEventListener("change", function () {
      if (!chatFileInput.files || chatFileInput.files.length === 0) return;
      const newFiles = Array.from(chatFileInput.files);
      chatAttachedFiles = chatAttachedFiles.concat(newFiles);
      chatFileInput.value = "";
      renderChatAttached();
    });
  }

  function renderChatAttached() {
    if (!chatAttachedEl) return;
    if (chatAttachedFiles.length === 0) {
      chatAttachedEl.innerHTML = "";
      hide(chatAttachedEl);
      return;
    }
    const names = chatAttachedFiles.map(function (f) { return f.name; }).join(", ");
    chatAttachedEl.textContent = "Attached: " + names;
    chatAttachedEl.classList.remove("hidden");
    show(chatAttachedEl);
  }

  function clearChatAttached() {
    chatAttachedFiles = [];
    if (chatAttachedEl) {
      chatAttachedEl.innerHTML = "";
      hide(chatAttachedEl);
    }
  }

  // Feature card click: prefill input with suggestion
  messagesEl.addEventListener("click", function (e) {
    const card = e.target.closest(".feature-card");
    if (!card || !messageInput) return;
    const suggestion = card.getAttribute("data-suggestion");
    if (suggestion) {
      messageInput.value = suggestion;
      messageInput.style.height = "auto";
      messageInput.style.height = messageInput.scrollHeight + "px";
      messageInput.focus();
    }
  });

  async function submitChat() {
    const text = messageInput.value.trim();
    const filesToSend = chatAttachedFiles ? chatAttachedFiles.slice() : [];
    const hasFiles = filesToSend.length > 0;
    if ((!text && !hasFiles) || isStreaming) return;

    const targetRole = (targetRoleInput.value || "").trim() || null;

    // Clear & reset (clear attached after we've copied the list)
    const messageToSend = text || (hasFiles ? "I've attached my resume." : "");
    messageInput.value = "";
    messageInput.style.height = "auto";
    clearChatAttached();
    sendBtn.disabled = true;
    isStreaming = true;
    hideToolStatus();

    const hadNoProfile = !profileStatus.exists;
    appendMessage("user", messageToSend, true);
    const typingEl = addTypingIndicator();
    scrollToBottom();

    let accum = "";
    let assistantBubble = null;
    let assistantRow = null;
    let typingRemoved = false;

    try {
      let r;
      if (hasFiles) {
        const formData = new FormData();
        formData.append("message", messageToSend);
        formData.append("session_id", sessionId);
        formData.append("profile_id", selectedProfileId || "");
        if (targetRole) formData.append("target_role", targetRole);
        filesToSend.forEach(function (f) { formData.append("files", f); });
        r = await fetch(API + "/chat", { method: "POST", body: formData });
      } else {
        r = await fetch(API + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: messageToSend,
            session_id: sessionId,
            profile_id: selectedProfileId || null,
            target_role: targetRole,
          }),
        });
      }

      if (!r.ok) {
        const err = await r.json().catch(function () { return {}; });
        removeTypingIndicator(typingEl);
        appendMessage("assistant", err.detail || err.message || "Request failed.", true);
        finishStream();
        return;
      }

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6);
          if (raw === "" || raw === "[DONE]") continue;

          let obj;
          try { obj = JSON.parse(raw); } catch (_) { continue; }

          if (obj.tool_call) {
            const toolName = obj.tool_call;
            const args = obj.args || {};
            const label = args.company
              ? "Researching " + args.company + "…"
              : toolName.replace(/_/g, " ") + "…";
            showToolStatus(label);
          }

          if (obj.token) {
            if (!typingRemoved) {
              removeTypingIndicator(typingEl);
              typingRemoved = true;
              // Create assistant bubble
              const result = appendMessage("assistant", "", true);
              assistantRow = result.row;
              assistantBubble = result.bubble;
            }
            accum += obj.token;
            assistantBubble.innerHTML = renderMarkdown(accum);
            scrollToBottom();
          }

          if (obj.done) {
            hideToolStatus();
            if (hadNoProfile) {
              fetchProfileStatus().then(function (status) {
                profileStatus = status;
                if (profileStatus.exists && profileStatus.profiles && profileStatus.profiles.length) {
                  selectedProfileId = profileStatus.default_profile_id || profileStatus.profiles[0].id;
                  sessionStorage.setItem("studia_profile_id", selectedProfileId);
                  profileSelect.innerHTML = "";
                  profileStatus.profiles.forEach(function (p) {
                    const opt = document.createElement("option");
                    opt.value = p.id;
                    opt.textContent = p.label || p.id;
                    if (p.id === selectedProfileId) opt.selected = true;
                    profileSelect.appendChild(opt);
                  });
                }
              }).catch(function () {});
            }
            break;
          }
        }
      }

      // Handle case: stream ended without any tokens (empty response)
      if (!typingRemoved) {
        removeTypingIndicator(typingEl);
        typingRemoved = true;
      }

    } catch (err) {
      removeTypingIndicator(typingEl);
      appendMessage("assistant", "Connection error: " + (err.message || "unknown"), true);
    }

    finishStream();
  }

  function finishStream() {
    hideToolStatus();
    isStreaming = false;
    sendBtn.disabled = false;
    messageInput.focus();
  }

  // ── New chat ───────────────────────────────────────────────────────────
  newChatBtn.addEventListener("click", function () {
    sessionId = "web-" + Math.random().toString(36).slice(2);
    sessionStorage.setItem("studia_session_id", sessionId);
    messagesEl.innerHTML = "";
    messagesEl.appendChild(emptyState);
    show(emptyState);
    isStreaming = false;
    hideToolStatus();
    sendBtn.disabled = false;
    messageInput.value = "";
    messageInput.style.height = "auto";
  });

  // ── Progress panel ─────────────────────────────────────────────────────
  progressBtn.addEventListener("click", openProgress);
  closeProgressBtn.addEventListener("click", closeProgress);
  progressBackdrop.addEventListener("click", closeProgress);
  refreshProgressBtn.addEventListener("click", function () {
    loadProgress();
  });

  function openProgress() {
    show(progressBackdrop);
    progressPanel.classList.add("open");
    loadProgress();
  }

  function closeProgress() {
    hide(progressBackdrop);
    progressPanel.classList.remove("open");
  }

  async function loadProgress() {
    weakList.innerHTML  = "<p class=\"panel-empty\">Loading…</p>";
    strongList.innerHTML = "<p class=\"panel-empty\">Loading…</p>";
    hide(suggestedCard);
    show(suggestedEmpty);

    try {
      const url = API + "/progress" + (selectedProfileId ? "?profile_id=" + encodeURIComponent(selectedProfileId) : "");
      const r = await fetch(url);
      if (!r.ok) {
        weakList.innerHTML = "<p class=\"panel-empty\">Failed to load</p>";
        strongList.innerHTML = "";
        return;
      }
      const data = await r.json();
      renderProgress(data);
    } catch (err) {
      weakList.innerHTML = "<p class=\"panel-empty\">Cannot reach server</p>";
      strongList.innerHTML = "";
    }
  }

  function renderProgress(data) {
    // Suggested next
    if (data.suggested_next && data.suggested_next_label) {
      suggestedLabel.textContent = data.suggested_next_label;
      show(suggestedCard);
      hide(suggestedEmpty);
      suggestedCard.onclick = function () {
        closeProgress();
        messageInput.value = "Let's practice " + data.suggested_next_label;
        messageInput.style.height = "auto";
        messageInput.style.height = messageInput.scrollHeight + "px";
        messageInput.focus();
      };
    } else {
      hide(suggestedCard);
      show(suggestedEmpty);
    }

    // Weak topics
    if (data.weak && data.weak.length > 0) {
      weakList.innerHTML = "";
      data.weak.forEach(function (t) { weakList.appendChild(buildTopicTile(t, "weak")); });
    } else {
      weakList.innerHTML = "<p class=\"panel-empty\">No weak areas tracked yet</p>";
    }

    // Strong topics
    if (data.strong && data.strong.length > 0) {
      strongList.innerHTML = "";
      data.strong.forEach(function (t) { strongList.appendChild(buildTopicTile(t, "strong")); });
    } else {
      strongList.innerHTML = "<p class=\"panel-empty\">No strong areas tracked yet</p>";
    }
  }

  function buildTopicTile(topic, kind) {
    const score = typeof topic.score === "number" ? topic.score : 0.5;
    const pct = Math.round(score * 100);

    let barClass = "mid";
    if (score < 0.4) barClass = "weak";
    else if (score >= 0.7) barClass = "strong";

    const tile = document.createElement("div");
    tile.className = "topic-tile";
    tile.innerHTML =
      "<div class=\"topic-tile-header\">" +
        "<span class=\"topic-tile-label\">" + escapeHtml(topic.label || topic.id) + "</span>" +
        "<span class=\"topic-tile-score\">" + pct + "%</span>" +
      "</div>" +
      "<div class=\"topic-bar-track\">" +
        "<div class=\"topic-bar " + barClass + "\" style=\"width:0%\"></div>" +
      "</div>";

    // Animate bar after paint
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        const bar = tile.querySelector(".topic-bar");
        if (bar) bar.style.width = pct + "%";
      });
    });

    tile.addEventListener("click", function () {
      closeProgress();
      messageInput.value = "Let's practice " + (topic.label || topic.id);
      messageInput.style.height = "auto";
      messageInput.style.height = messageInput.scrollHeight + "px";
      messageInput.focus();
    });

    return tile;
  }

  // ── Fetch profile status ───────────────────────────────────────────────
  async function fetchProfileStatus() {
    const r = await fetch(API + "/profile/status");
    if (!r.ok) throw new Error("Failed to load profile status");
    return r.json();
  }

  // ── Boot ───────────────────────────────────────────────────────────────
  (async function init() {
    try {
      profileStatus = await fetchProfileStatus();
      renderScreens();
    } catch (err) {
      loadingEl.innerHTML =
        "<div style=\"text-align:center;padding:2rem;color:var(--muted)\">" +
        "<p style=\"font-size:1rem;margin-bottom:0.5rem;color:var(--error)\">Cannot reach server</p>" +
        "<p style=\"font-size:0.85rem\">Is the backend running? <code style=\"background:var(--card);padding:2px 6px;border-radius:4px;font-size:0.8rem\">cd backend &amp;&amp; python -m uvicorn main:app --reload</code></p>" +
        "</div>";
    }
  })();

})();
