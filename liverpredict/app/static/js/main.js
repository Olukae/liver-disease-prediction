// =====================================================================
// LiverPredict AI — main.js
// =====================================================================
(function () {
  "use strict";

  /* ---------------------------------------------------------------- *
   * Toast notifications
   * ---------------------------------------------------------------- */
  const toastStack = document.getElementById("toast-stack");
  const ICONS = {
    success: "fa-circle-check", danger: "fa-circle-exclamation",
    info: "fa-circle-info", warning: "fa-triangle-exclamation",
  };

  function showToast(message, category = "info", timeout = 4500) {
    if (!toastStack) return;
    const el = document.createElement("div");
    el.className = `toast-item ${category}`;
    el.innerHTML = `<i class="fa-solid ${ICONS[category] || ICONS.info}"></i><span>${message}</span>`;
    toastStack.appendChild(el);
    setTimeout(() => {
      el.style.animation = "toastOut .3s ease forwards";
      setTimeout(() => el.remove(), 300);
    }, timeout);
  }
  window.showToast = showToast;

  document.addEventListener("DOMContentLoaded", () => {
    const flashData = document.getElementById("flashData");
    if (flashData) {
      try {
        const messages = JSON.parse(flashData.dataset.messages || "[]");
        messages.forEach(([category, msg], i) => {
          setTimeout(() => showToast(msg, category === "message" ? "info" : category), i * 150);
        });
      } catch (e) { /* noop */ }
    }
  });

  /* ---------------------------------------------------------------- *
   * Dark mode
   * ---------------------------------------------------------------- */
  const root = document.documentElement;
  const darkToggle = document.getElementById("darkModeToggle");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (darkToggle) {
      darkToggle.innerHTML = theme === "dark"
        ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    }
  }

  const savedTheme = localStorage.getItem("lp-theme") ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  applyTheme(savedTheme);

  if (darkToggle) {
    darkToggle.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem("lp-theme", next);
      applyTheme(next);
    });
  }

  /* ---------------------------------------------------------------- *
   * Mobile sidebar toggle
   * ---------------------------------------------------------------- */
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
        sidebar.classList.remove("open");
      }
    });
  }

  /* ---------------------------------------------------------------- *
   * AI Health Assistant chat widget
   * ---------------------------------------------------------------- */
  const chatToggle = document.getElementById("chatToggle");
  const chatWidget = document.getElementById("chatWidget");
  const chatClose = document.getElementById("chatClose");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatBody = document.getElementById("chatBody");
  const voiceBtn = document.getElementById("voiceBtn");

  function addChatMessage(text, who) {
    const div = document.createElement("div");
    div.className = `chat-msg ${who}`;
    div.textContent = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  if (chatToggle && chatWidget) {
    chatToggle.addEventListener("click", () => chatWidget.classList.toggle("open"));
    chatClose.addEventListener("click", () => chatWidget.classList.remove("open"));
  }

  if (chatForm) {
    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;
      addChatMessage(message, "user");
      chatInput.value = "";

      const typing = document.createElement("div");
      typing.className = "chat-msg bot";
      typing.innerHTML = '<i class="fa-solid fa-ellipsis fa-fade"></i>';
      chatBody.appendChild(typing);
      chatBody.scrollTop = chatBody.scrollHeight;

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });
        const data = await res.json();
        typing.remove();
        addChatMessage(data.reply, "bot");
      } catch (err) {
        typing.remove();
        addChatMessage("Sorry, I couldn't reach the assistant right now.", "bot");
      }
    });
  }

  // Voice input (Web Speech API) for the chat box
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (voiceBtn) {
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      let listening = false;

      voiceBtn.addEventListener("click", () => {
        if (listening) { recognition.stop(); return; }
        recognition.start();
        listening = true;
        voiceBtn.classList.add("recording");
      });
      recognition.onresult = (e) => {
        chatInput.value = e.results[0][0].transcript;
      };
      recognition.onend = () => { listening = false; voiceBtn.classList.remove("recording"); };
      recognition.onerror = () => { listening = false; voiceBtn.classList.remove("recording"); };
    } else {
      voiceBtn.addEventListener("click", () => showToast("Voice input isn't supported in this browser.", "warning"));
    }
  }

  /* ---------------------------------------------------------------- *
   * Generic voice input for any field: data-voice-input="fieldId"
   * ---------------------------------------------------------------- */
  document.querySelectorAll("[data-voice-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-voice-target");
      const target = document.getElementById(targetId);
      if (!SpeechRecognition || !target) {
        showToast("Voice input isn't supported in this browser.", "warning");
        return;
      }
      const rec = new SpeechRecognition();
      rec.lang = "en-US";
      btn.classList.add("recording");
      rec.start();
      rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        const numeric = transcript.match(/[\d.]+/);
        target.value = numeric ? numeric[0] : transcript;
        target.dispatchEvent(new Event("input"));
      };
      rec.onend = () => btn.classList.remove("recording");
      rec.onerror = () => btn.classList.remove("recording");
    });
  });

  /* ---------------------------------------------------------------- *
   * Confidence ring gauge — animates stroke based on data-percent
   * ---------------------------------------------------------------- */
  document.querySelectorAll(".confidence-ring").forEach((ring) => {
    const percent = parseFloat(ring.dataset.percent || "0");
    const circle = ring.querySelector(".ring-fg");
    if (!circle) return;
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;
    requestAnimationFrame(() => {
      const offset = circumference - (percent / 100) * circumference;
      circle.style.strokeDashoffset = offset;
    });
  });

  /* ---------------------------------------------------------------- *
   * Form submit loading state
   * ---------------------------------------------------------------- */
  document.querySelectorAll("form[data-loading-btn]").forEach((form) => {
    form.addEventListener("submit", () => {
      if (!form.checkValidity()) return;
      const btn = form.querySelector("[data-loading-btn] , button[type=submit]");
      const submitBtn = form.querySelector("button[type=submit]");
      if (submitBtn) {
        submitBtn.dataset.originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        submitBtn.disabled = true;
      }
    });
  });

  /* ---------------------------------------------------------------- *
   * Real-time validation styling (Bootstrap-friendly)
   * ---------------------------------------------------------------- */
  document.querySelectorAll(".validate-field").forEach((input) => {
    input.addEventListener("input", () => {
      if (input.checkValidity()) {
        input.classList.remove("field-invalid");
        input.classList.add("field-valid");
      } else {
        input.classList.remove("field-valid");
        input.classList.add("field-invalid");
      }
    });
  });
})();
