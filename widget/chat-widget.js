/**
 * chat-widget.js – Self-contained embeddable chat widget.
 *
 * How to embed on any website:
 *
 *   <script>
 *     window.ChatWidgetConfig = {
 *       apiUrl: "https://your-api-server.com",   // FastAPI backend URL
 *       title:  "Support Chat",                   // Header title (optional)
 *       primaryColor: "#4f46e5",                  // Brand colour (optional)
 *     };
 *   </script>
 *   <script src="chat-widget.js" defer></script>
 *
 * The script creates a floating button in the bottom-right corner.
 * Clicking it opens a chat window that talks to the RAG API.
 */
(function () {
  "use strict";

  // ── Configuration ───────────────────────────────────────────────────────────
  const config = Object.assign(
    {
      apiUrl: "http://localhost:8000",
      title: "Chat Assistant",
      primaryColor: "#4f46e5",
      bubbleSize: "56px",
    },
    window.ChatWidgetConfig || {}
  );

  // ── State ───────────────────────────────────────────────────────────────────
  const history = []; // [{role, content}, ...]
  let isOpen = false;

  // ── Styles ───────────────────────────────────────────────────────────────────
  const css = `
    #cw-root * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }

    #cw-bubble {
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      width: ${config.bubbleSize}; height: ${config.bubbleSize};
      background: ${config.primaryColor};
      border-radius: 50%; cursor: pointer; border: none;
      box-shadow: 0 4px 14px rgba(0,0,0,.25);
      display: flex; align-items: center; justify-content: center;
      transition: transform .2s;
    }
    #cw-bubble:hover { transform: scale(1.08); }
    #cw-bubble svg { width: 26px; height: 26px; fill: #fff; }

    #cw-window {
      position: fixed; bottom: 92px; right: 24px; z-index: 9998;
      width: 360px; max-height: 520px;
      background: #fff; border-radius: 16px;
      box-shadow: 0 8px 30px rgba(0,0,0,.18);
      display: flex; flex-direction: column;
      overflow: hidden;
      transform: scale(0); transform-origin: bottom right;
      transition: transform .2s ease, opacity .2s ease;
      opacity: 0; pointer-events: none;
    }
    #cw-window.cw-open {
      transform: scale(1); opacity: 1; pointer-events: all;
    }

    #cw-header {
      background: ${config.primaryColor}; color: #fff;
      padding: 14px 16px; font-weight: 600; font-size: 15px;
      display: flex; align-items: center; justify-content: space-between;
    }
    #cw-close {
      background: transparent; border: none; color: #fff;
      font-size: 20px; cursor: pointer; line-height: 1; padding: 0;
    }

    #cw-messages {
      flex: 1; overflow-y: auto; padding: 16px;
      display: flex; flex-direction: column; gap: 10px;
      min-height: 0;
    }

    .cw-msg {
      max-width: 80%; padding: 10px 14px; border-radius: 14px;
      font-size: 14px; line-height: 1.5; word-wrap: break-word;
      white-space: pre-wrap;
    }
    .cw-msg-user {
      background: ${config.primaryColor}; color: #fff;
      align-self: flex-end; border-bottom-right-radius: 4px;
    }
    .cw-msg-bot {
      background: #f1f5f9; color: #1e293b;
      align-self: flex-start; border-bottom-left-radius: 4px;
    }
    .cw-msg-typing { color: #94a3b8; font-style: italic; }

    #cw-input-area {
      display: flex; gap: 8px; padding: 12px;
      border-top: 1px solid #e2e8f0;
    }
    #cw-input {
      flex: 1; border: 1px solid #cbd5e1; border-radius: 8px;
      padding: 8px 12px; font-size: 14px; outline: none;
      resize: none; line-height: 1.4;
    }
    #cw-input:focus { border-color: ${config.primaryColor}; }
    #cw-send {
      background: ${config.primaryColor}; color: #fff;
      border: none; border-radius: 8px; padding: 8px 14px;
      font-size: 14px; cursor: pointer; white-space: nowrap;
      transition: opacity .15s;
    }
    #cw-send:disabled { opacity: .5; cursor: default; }
  `;

  // ── DOM helpers ──────────────────────────────────────────────────────────────
  function injectStyles() {
    const style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
  }

  function buildDOM() {
    const root = document.createElement("div");
    root.id = "cw-root";

    // Floating bubble button
    const bubble = document.createElement("button");
    bubble.id = "cw-bubble";
    bubble.setAttribute("aria-label", "Open chat");
    bubble.innerHTML = `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4C2.9 2 2 2.9 2 4v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
      </svg>`;

    // Chat window
    const win = document.createElement("div");
    win.id = "cw-window";
    win.setAttribute("role", "dialog");
    win.setAttribute("aria-label", config.title);

    win.innerHTML = `
      <div id="cw-header">
        <span>${escapeHtml(config.title)}</span>
        <button id="cw-close" aria-label="Close chat">&#x2715;</button>
      </div>
      <div id="cw-messages" aria-live="polite"></div>
      <div id="cw-input-area">
        <textarea id="cw-input" rows="1" placeholder="Type your message…"
          aria-label="Message input"></textarea>
        <button id="cw-send">Send</button>
      </div>`;

    root.appendChild(bubble);
    root.appendChild(win);
    document.body.appendChild(root);

    return {
      bubble,
      win,
      messages: win.querySelector("#cw-messages"),
      input: win.querySelector("#cw-input"),
      send: win.querySelector("#cw-send"),
      close: win.querySelector("#cw-close"),
    };
  }

  // ── Utilities ────────────────────────────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function appendMessage(container, role, text) {
    const div = document.createElement("div");
    div.className = `cw-msg cw-msg-${role === "user" ? "user" : "bot"}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function autoResizeTextarea(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  // ── API calls ────────────────────────────────────────────────────────────────
  async function sendMessage(message, messagesEl, sendBtn, inputEl) {
    sendBtn.disabled = true;

    appendMessage(messagesEl, "user", message);
    history.push({ role: "user", content: message });

    const typingEl = appendMessage(messagesEl, "bot", "Thinking…");
    typingEl.classList.add("cw-msg-typing");

    try {
      const res = await fetch(`${config.apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history: history.slice(0, -1) }),
      });

      if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
      }
      const data = await res.json();
      const reply = data.reply || "Sorry, I couldn't get a response.";

      typingEl.classList.remove("cw-msg-typing");
      typingEl.textContent = reply;
      history.push({ role: "assistant", content: reply });
    } catch (err) {
      typingEl.classList.remove("cw-msg-typing");
      typingEl.textContent =
        "⚠️ Could not reach the server. Please try again later.";
      console.error("[ChatWidget]", err);
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  // ── Bootstrap ────────────────────────────────────────────────────────────────
  function init() {
    injectStyles();
    const els = buildDOM();

    // Toggle open/close
    function toggleOpen() {
      isOpen = !isOpen;
      els.win.classList.toggle("cw-open", isOpen);
      els.bubble.setAttribute("aria-expanded", String(isOpen));
      if (isOpen) {
        els.input.focus();
        // Show a greeting on first open
        if (els.messages.children.length === 0) {
          appendMessage(
            els.messages,
            "bot",
            `👋 Hi there! I'm ${config.title}. Ask me anything about this website.`
          );
        }
      }
    }

    els.bubble.addEventListener("click", toggleOpen);
    els.close.addEventListener("click", toggleOpen);

    // Send on button click
    els.send.addEventListener("click", function () {
      const msg = els.input.value.trim();
      if (!msg) return;
      els.input.value = "";
      autoResizeTextarea(els.input);
      sendMessage(msg, els.messages, els.send, els.input);
    });

    // Send on Enter (Shift+Enter = newline)
    els.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        els.send.click();
      }
    });

    // Auto-resize textarea
    els.input.addEventListener("input", function () {
      autoResizeTextarea(els.input);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
