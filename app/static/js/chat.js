/**
 * chat.js
 * =======
 * Gestión del chat en el cliente:
 *   - Auto-resize del textarea
 *   - Envío de mensajes con Enter (Shift+Enter = nueva línea)
 *   - Petición AJAX al endpoint /api/conversations/{id}/messages
 *   - Inserción dinámica de burbujas de mensajes en el DOM
 *   - Indicador de escritura mientras el modelo responde
 *   - Actualización del título en el sidebar
 */

(function () {
  "use strict";

  // ── Elementos del DOM ──────────────────────────────────────────────────────
  const form            = document.getElementById("messageForm");
  const input           = document.getElementById("messageInput");
  const sendButton      = document.getElementById("sendButton");
  const messagesArea    = document.getElementById("messagesArea");
  const typingIndicator = document.getElementById("typingIndicator");
  const conversationId  = (form && form.dataset.conversationId) || window.CONVERSATION_ID;

  // Sólo actuar si estamos en la vista de conversación
  if (!form || !input || !messagesArea) return;

  // ── Scroll al último mensaje ───────────────────────────────────────────────
  function scrollToBottom(smooth) {
    messagesArea.scrollTo({
      top: messagesArea.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });
  }

  // Scroll inicial sin animación para no mostrar el desplazamiento al cargar
  scrollToBottom(false);

  // ── Auto-resize del textarea ───────────────────────────────────────────────
  function autoResize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  }
  input.addEventListener("input", autoResize);

  // ── Enter para enviar; Shift+Enter para nueva línea ───────────────────────
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendButton.disabled && input.value.trim()) {
        form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
      }
    }
  });

  // ── Formateo de hora (HH:MM) ───────────────────────────────────────────────
  function formatTime(isoString) {
    return new Date(isoString).toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // ── Escape de HTML para evitar XSS ────────────────────────────────────────
  function escapeHtml(text) {
    const el = document.createElement("div");
    el.appendChild(document.createTextNode(text));
    return el.innerHTML;
  }

  // ── Construir elemento de burbuja de mensaje ───────────────────────────────
  function buildMessageEl(role, content, timeStr) {
    const userIcon = `
      <svg viewBox="0 0 24 24" fill="none" class="role-icon">
        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5"/>
        <path d="M4 20c0-4 3.582-7 8-7s8 3 8 7"
              stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;

    const aiIcon = `
      <svg viewBox="0 0 24 24" fill="none" class="role-icon">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
        <path d="M8 12h8M12 8v8"
              stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;

    const icon = role === "user" ? userIcon : aiIcon;

    // Preservar saltos de línea; el contenido ya está escapado
    const html = escapeHtml(content).replace(/\n/g, "<br>");

    const div = document.createElement("div");
    div.className = `message message--${role}`;
    div.innerHTML = `
      <div class="message-bubble">
        <div class="message-content">${html}</div>
        <div class="message-time">${icon}${timeStr}</div>
      </div>`;
    return div;
  }

  // ── Eliminar el estado "conversación vacía" si existe ─────────────────────
  function removeEmptyState() {
    const empty = document.getElementById("emptyState");
    if (empty) empty.remove();
  }

  // ── Actualizar el título en el sidebar y en la cabecera del chat ──────────
  function updateTitle(newTitle) {
    const sidebarTitle = document.querySelector(
      ".conversation-item.active .conversation-title"
    );
    if (sidebarTitle) sidebarTitle.textContent = newTitle;

    const chatTitle = document.getElementById("chatTitle");
    if (chatTitle) chatTitle.textContent = newTitle;

    document.title = `${newTitle} — Azure AI Chat`;
  }

  // ── Bloquear / desbloquear la UI ───────────────────────────────────────────
  function setUILocked(locked) {
    sendButton.disabled = locked;
    input.disabled      = locked;
    if (!locked) input.focus();
  }

  // ── Envío del mensaje via AJAX ─────────────────────────────────────────────
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const content = input.value.trim();
    if (!content || !conversationId) return;

    setUILocked(true);
    input.value = "";
    autoResize();
    removeEmptyState();

    // Insertar burbuja del usuario de forma optimista
    const nowIso  = new Date().toISOString();
    const userEl  = buildMessageEl("user", content, formatTime(nowIso));
    messagesArea.insertBefore(userEl, typingIndicator);
    scrollToBottom(true);

    // Mostrar indicador de escritura
    typingIndicator.style.display = "block";
    scrollToBottom(true);

    try {
      const res = await fetch(
        `/api/conversations/${conversationId}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Error HTTP ${res.status}`);
      }

      const data = await res.json();

      // Actualizar hora real del mensaje del usuario (la del servidor)
      if (data.user_message) {
        const timeEl = userEl.querySelector(".message-time");
        if (timeEl) {
          timeEl.innerHTML = timeEl.innerHTML.replace(
            /\d{2}:\d{2}/,
            formatTime(data.user_message.created_at)
          );
        }
      }

      // Ocultar indicador y mostrar respuesta del asistente
      typingIndicator.style.display = "none";
      const aiEl = buildMessageEl(
        "assistant",
        data.assistant_message.content,
        formatTime(data.assistant_message.created_at)
      );
      messagesArea.insertBefore(aiEl, typingIndicator);
      scrollToBottom(true);

      // Actualizar título si es el primer mensaje
      if (data.new_title) updateTitle(data.new_title);

    } catch (err) {
      typingIndicator.style.display = "none";

      // Mostrar el error en una burbuja roja
      const errEl = buildMessageEl(
        "assistant",
        `⚠️ ${err.message}`,
        formatTime(new Date().toISOString())
      );
      const bubble = errEl.querySelector(".message-bubble");
      if (bubble) {
        bubble.style.background    = "#fef2f2";
        bubble.style.borderColor   = "#fca5a5";
        bubble.style.border        = "1px solid #fca5a5";
      }
      const contentEl = errEl.querySelector(".message-content");
      if (contentEl) contentEl.style.color = "#dc2626";

      messagesArea.insertBefore(errEl, typingIndicator);
      scrollToBottom(true);
    } finally {
      setUILocked(false);
    }
  });

})();
