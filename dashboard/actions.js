/*
 * actions.js — Commands panel: operator types a natural-language action,
 * we ship it over the dashboard's existing WebSocket, and render status
 * frames the server sends back.
 *
 * Message shapes:
 *   client → server:  {type:"action", text, ts}
 *                     {type:"stop", ts}
 *   server → client:  {type:"status", phase:"planning|executing|done|error|idle",
 *                      text, plan?, step?}
 *
 * The panel is intentionally small and dependency-free — matches the
 * Recon* namespace pattern used by intel.js / telemetry.js.
 */
(function (global) {
  const MAX_ENTRIES = 60;

  let els = null;
  let sendFn = null;

  function timestamp() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function appendLog(role, text) {
    if (!els || !els.log) return;
    // Drop the "empty" placeholder the first time a real entry lands.
    const placeholder = els.log.querySelector("li.cmd-empty");
    if (placeholder) placeholder.remove();

    const li = document.createElement("li");
    li.className = `cmd-${role}`;
    li.innerHTML =
      `<span class="cmd-ts">${timestamp()}</span>` +
      `<span class="cmd-msg">${escapeHtml(text)}</span>`;
    els.log.appendChild(li);

    while (els.log.children.length > MAX_ENTRIES) {
      els.log.removeChild(els.log.firstChild);
    }
    els.log.scrollTop = els.log.scrollHeight;
  }

  function setMeta(text) {
    if (els && els.meta) els.meta.textContent = text || "";
  }

  function seedPlaceholder() {
    // Intentionally empty — the log starts blank.
  }

  function init(elements, send) {
    els = elements;
    sendFn = send || null;
    seedPlaceholder();

    if (els.form) {
      els.form.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = (els.input && els.input.value.trim()) || "";
        if (!text) return;
        if (!sendFn) {
          appendLog("error", "Not connected to robot (no WebSocket)");
          return;
        }
        const ok = sendFn({ type: "action", text, ts: Date.now() });
        if (ok === false) {
          appendLog("error", "WebSocket not open — command not sent");
          return;
        }
        appendLog("user", text);
        setMeta("Sent");
        if (els.input) els.input.value = "";
      });
    }

    if (els.stop) {
      els.stop.addEventListener("click", () => {
        if (!sendFn) {
          appendLog("error", "Not connected to robot (no WebSocket)");
          return;
        }
        sendFn({ type: "stop", ts: Date.now() });
        appendLog("system", "STOP sent");
        setMeta("Stopping");
      });
    }

    // Ctrl/Cmd+Enter submits from within the textarea for fast-iterating.
    if (els.input) {
      els.input.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
          e.preventDefault();
          if (els.form) {
            els.form.dispatchEvent(
              new Event("submit", { cancelable: true, bubbles: true }),
            );
          }
        }
      });
    }

    // Voice input via Web Speech API (Chrome / Edge).
    const micBtn = document.getElementById("commands-mic");
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (micBtn && SR) {
      const recog = new SR();
      recog.lang = "en-US";
      recog.interimResults = false;
      recog.maxAlternatives = 1;
      let listening = false;

      micBtn.addEventListener("click", () => {
        if (!listening) {
          try {
            recog.start();
          } catch (e) {
            appendLog("error", "Voice: could not start — " + e.message);
            return;
          }
          micBtn.textContent = "REC";
          micBtn.classList.add("btn-mic-active");
          listening = true;
        } else {
          recog.stop();
        }
      });

      recog.onresult = (e) => {
        const text = e.results[0][0].transcript.trim();
        if (!text) return;
        if (!sendFn) {
          appendLog("error", "Not connected — voice command not sent");
          return;
        }
        sendFn({ type: "action", text, ts: Date.now() });
        appendLog("user", "[voice] " + text);
        setMeta("Sent (voice)");
      };

      recog.onend = () => {
        listening = false;
        micBtn.textContent = "MIC";
        micBtn.classList.remove("btn-mic-active");
      };

      recog.onerror = (e) => {
        appendLog("error", "Voice error: " + e.error);
        listening = false;
        micBtn.textContent = "MIC";
        micBtn.classList.remove("btn-mic-active");
      };
    } else if (micBtn) {
      micBtn.disabled = true;
      micBtn.title = "Speech recognition not supported in this browser (use Chrome/Edge)";
    }
  }

  function setSender(send) {
    sendFn = send || null;
  }

  function applyStatus(msg) {
    if (!msg || typeof msg !== "object") return;
    const phase = msg.phase || "info";
    setMeta(phase.charAt(0).toUpperCase() + phase.slice(1));
    const role =
      phase === "error"
        ? "error"
        : phase === "done"
          ? "system"
          : "bot";
    const text = msg.text || phase;
    appendLog(role, text);
    if (Array.isArray(msg.plan) && msg.plan.length) {
      const summary = msg.plan
        .map((s) => {
          if (!s || !s.op) return "?";
          const arg =
            s.meters != null
              ? `${s.meters}m`
              : s.radians != null
                ? `${s.radians}rad`
                : s.seconds != null
                  ? `${s.seconds}s`
                  : "";
          return `${s.op}${arg ? "(" + arg + ")" : ""}`;
        })
        .join(" → ");
      appendLog("bot", `plan: ${summary}`);
    }
  }

  global.ReconActions = { init, setSender, applyStatus };
})(window);
