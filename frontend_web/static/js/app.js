/**
 * Application Frontend Logic
 * Handles Toast Notifications and UI interactions.
 */

// ==========================================================================
// Toast Notification System
// ==========================================================================
function showToast(message, type = "info", duration = 4000) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Trigger entrance animation
    requestAnimationFrame(() => {
        toast.classList.add("toast-visible");
    });

    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.remove("toast-visible");
        toast.addEventListener("transitionend", () => toast.remove(), { once: true });
        // Fallback removal if transitionend doesn't fire
        setTimeout(() => toast.remove(), 500);
    }, duration);
}

// Check for flash messages rendered in HTML data attributes
document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll('.flash-message-data');
    flashMessages.forEach(msg => {
        const category = msg.dataset.category; // e.g., 'danger', 'success'
        const message = msg.dataset.message;
        
        // Map Flask categories to Toast categories
        let toastType = "info";
        if (category === "danger" || category === "error") toastType = "error";
        if (category === "success") toastType = "success";
        if (category === "warning") toastType = "warning";

        showToast(message, toastType);
    });
});

// ==========================================================================
// Auth Toggle Logic (Landing Page)
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const toggleContainer = document.getElementById("auth-toggle-container");
    if (!toggleContainer) return;

    const btnSignup = document.getElementById("btn-toggle-signup");
    const btnLogin = document.getElementById("btn-toggle-login");
    const authForm = document.getElementById("auth-form");
    const formAction = document.getElementById("form-action");
    const btnSubmitText = document.getElementById("btn-submit-text");

    if (btnSignup && btnLogin) {
        btnSignup.addEventListener("click", (e) => {
            e.preventDefault();
            toggleContainer.classList.remove("mode-login");
            btnSignup.classList.add("active");
            btnLogin.classList.remove("active");
            authForm.action = "/signup";
            formAction.value = "signup";
            btnSubmitText.textContent = "Create Account";
        });

        btnLogin.addEventListener("click", (e) => {
            e.preventDefault();
            toggleContainer.classList.add("mode-login");
            btnLogin.classList.add("active");
            btnSignup.classList.remove("active");
            authForm.action = "/login";
            formAction.value = "login";
            btnSubmitText.textContent = "Login";
        });
    }

    // Smooth scroll for explore button
    const btnExplore = document.getElementById("btn-explore-arch");
    if (btnExplore) {
        btnExplore.addEventListener("click", (e) => {
            e.preventDefault();
            const archSection = document.getElementById("architecture-section");
            if (archSection) {
                archSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
});

// ==========================================================================
// Global Project Chatbot
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("project-chatbot-launcher")) return;

    const contextNode = document.getElementById("chatbot-context");
    let pageContext = {
        page: window.location.pathname,
        title: document.title,
    };

    if (contextNode && contextNode.textContent) {
        try {
            pageContext = JSON.parse(contextNode.textContent);
        } catch (_) {
            // Keep default page context if JSON cannot be parsed.
        }
    }

    const launcher = document.createElement("button");
    launcher.id = "project-chatbot-launcher";
    launcher.className = "chatbot-launcher";
    launcher.setAttribute("type", "button");
    launcher.setAttribute("aria-label", "Open project assistant");
    launcher.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4v-4z" />
        </svg>
    `;

    const panel = document.createElement("aside");
    panel.id = "project-chatbot-panel";
    panel.className = "chatbot-panel";
    panel.innerHTML = `
        <div class="chatbot-header">
            <div>
                <div class="chatbot-title">Project Assistant</div>
                <div class="chatbot-subtitle">LOAN XAI SYSTEM only</div>
            </div>
            <button class="chatbot-reset" id="chatbot-reset-btn" type="button">Reset</button>
        </div>
        <div class="chatbot-messages" id="chatbot-messages"></div>
        <div class="chatbot-quick-actions" id="chatbot-quick-actions"></div>
        <form class="chatbot-input-wrap" id="chatbot-form">
            <input class="chatbot-input" id="chatbot-input" type="text" autocomplete="off" placeholder="Ask about this project..." />
            <button class="chatbot-send" id="chatbot-send" type="submit">Send</button>
        </form>
    `;

    document.body.appendChild(panel);
    document.body.appendChild(launcher);

    const messagesEl = document.getElementById("chatbot-messages");
    const quickActionsEl = document.getElementById("chatbot-quick-actions");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");
    const resetBtn = document.getElementById("chatbot-reset-btn");

    const quickActions = pageContext.page === "dashboard"
        ? [
            "Why is this applicant high risk?",
            "Which feature lowered risk the most?",
            "Explain SHAP vs LIME for this result",
            "How can this applicant reduce default risk?",
        ]
        : [
            "What does this project do?",
            "How does prediction work end to end?",
            "What is SHAP used for here?",
            "Which model can I select?",
        ];

    function addMessage(role, text) {
        const msg = document.createElement("div");
        msg.className = `chatbot-message ${role}`;
        msg.textContent = text;
        messagesEl.appendChild(msg);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function sendMessage(message) {
        const userText = String(message || "").trim();
        if (!userText) return;

        addMessage("user", userText);
        input.value = "";
        input.disabled = true;

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 90000);

            const response = await fetch("/api/chatbot/message", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userText,
                    page_context: pageContext,
                }),
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            const raw = await response.text();
            let payload = {};
            try {
                payload = raw ? JSON.parse(raw) : {};
            } catch (_) {
                payload = { reply: "Server returned an unexpected response format." };
            }

            if (!response.ok) {
                addMessage(
                    "assistant",
                    payload.error || payload.reply || `Unable to answer right now (HTTP ${response.status}).`
                );
            } else {
                addMessage("assistant", payload.reply || "No response generated.");
            }
        } catch (error) {
            if (error && error.name === "AbortError") {
                addMessage("assistant", "The model is taking longer than expected. Please try again in a moment.");
            } else {
                addMessage("assistant", "Connection error. Please try again.");
            }
        } finally {
            input.disabled = false;
            input.focus();
        }
    }

    quickActions.forEach((label) => {
        const btn = document.createElement("button");
        btn.className = "chatbot-quick-btn";
        btn.type = "button";
        btn.textContent = label;
        btn.addEventListener("click", () => sendMessage(label));
        quickActionsEl.appendChild(btn);
    });

    addMessage(
        "assistant",
        pageContext.page === "dashboard"
            ? "I can explain this exact applicant result. Ask about risk drivers, SHAP/LIME, or improvement ideas."
            : "I am your LOAN XAI SYSTEM assistant. Ask me anything about this project."
    );

    launcher.addEventListener("click", () => {
        panel.classList.toggle("open");
        if (panel.classList.contains("open")) {
            input.focus();
        }
    });

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(input.value);
    });

    resetBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/chatbot/reset", { method: "POST" });
        } catch (_) {
            // Ignore reset errors and reset local UI anyway.
        }
        messagesEl.innerHTML = "";
        addMessage("assistant", "Chat reset. Ask a new question about LOAN XAI SYSTEM.");
    });
});
