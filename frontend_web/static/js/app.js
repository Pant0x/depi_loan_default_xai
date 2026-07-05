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
    launcher.setAttribute("aria-label", "Open Credit Officer chat");
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
                <div class="chatbot-title">Credit Officer</div>
                <div class="chatbot-subtitle">Powered by Audit Record · LightGBM</div>
            </div>
            <div class="chatbot-header-actions" style="display:flex;align-items:center;gap:0.45rem;">
                <button class="chatbot-tts-toggle chatbot-reset" id="chatbot-tts-toggle" type="button" aria-label="Enable voice narration" title="Voice narration off">🔇</button>
                <button class="chatbot-reset" id="chatbot-expand-toggle" type="button" aria-label="Toggle size" title="Expand chat">⛶</button>
                <button class="chatbot-reset" id="chatbot-reset-btn" type="button">Reset</button>
            </div>
        </div>
        <div class="chatbot-messages" id="chatbot-messages"></div>
        <div class="chatbot-quick-actions" id="chatbot-quick-actions"></div>
        <form class="chatbot-input-wrap" id="chatbot-form">
            <input class="chatbot-input" id="chatbot-input" type="text" autocomplete="off" placeholder="Ask the Credit Officer..." />
            <button class="chatbot-mic chatbot-send" id="chatbot-mic-btn" type="button" aria-label="Voice input" title="Speak your question" style="padding:0.65rem 0.75rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 14a3 3 0 003-3V7a3 3 0 10-6 0v4a3 3 0 003 3z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-14 0M12 19v3" />
                </svg>
            </button>
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
    const micBtn = document.getElementById("chatbot-mic-btn");
    const ttsToggleBtn = document.getElementById("chatbot-tts-toggle");
    const expandToggleBtn = document.getElementById("chatbot-expand-toggle");

    let isTTSEnabled = false;
    let speechRecognition = null;
    let isListening = false;

    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesisSupported = typeof window.speechSynthesis !== "undefined";

    if (!SpeechRecognitionCtor && micBtn) {
        micBtn.style.display = "none";
    }

    if (!speechSynthesisSupported && ttsToggleBtn) {
        ttsToggleBtn.style.display = "none";
    }

    function updateTTSToggleUI() {
        if (!ttsToggleBtn) return;
        ttsToggleBtn.textContent = isTTSEnabled ? "🔊" : "🔇";
        ttsToggleBtn.title = isTTSEnabled ? "Voice narration on" : "Voice narration off";
        ttsToggleBtn.setAttribute(
            "aria-label",
            isTTSEnabled ? "Disable voice narration" : "Enable voice narration"
        );
    }

    function speakAssistantResponse(text) {
        if (!isTTSEnabled || !speechSynthesisSupported) return;
        const content = String(text || "").trim();
        if (!content) return;

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(content);
        utterance.lang = "en-US";
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }

    if (ttsToggleBtn) {
        updateTTSToggleUI();
        ttsToggleBtn.addEventListener("click", () => {
            isTTSEnabled = !isTTSEnabled;
            if (!isTTSEnabled && speechSynthesisSupported) {
                window.speechSynthesis.cancel();
            }
            updateTTSToggleUI();
        });
    }

    function setMicListeningState(active) {
        isListening = active;
        if (!micBtn) return;
        micBtn.classList.toggle("chatbot-mic--listening", active);
        micBtn.style.background = active
            ? "linear-gradient(135deg, #ef4444, #dc2626)"
            : "";
        micBtn.title = active ? "Listening..." : "Speak your question";
        micBtn.setAttribute("aria-label", active ? "Listening for voice input" : "Voice input");
    }

    if (SpeechRecognitionCtor && micBtn) {
        speechRecognition = new SpeechRecognitionCtor();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;
        speechRecognition.lang = "en-US";

        speechRecognition.addEventListener("result", (event) => {
            const transcript = event.results?.[0]?.[0]?.transcript?.trim();
            if (transcript) {
                input.value = transcript;
                sendMessage(transcript);
            }
        });

        speechRecognition.addEventListener("end", () => {
            setMicListeningState(false);
        });

        speechRecognition.addEventListener("error", () => {
            setMicListeningState(false);
        });

        micBtn.addEventListener("click", () => {
            if (isListening) {
                speechRecognition.stop();
                setMicListeningState(false);
                return;
            }
            try {
                setMicListeningState(true);
                speechRecognition.start();
            } catch (_) {
                setMicListeningState(false);
            }
        });
    }

    const quickActions = pageContext.page === "dashboard"
        ? [
            "Explain the credit decision for this applicant",
            "What are the main risk factors in this profile?",
            "How does this applicant compare to a low-risk profile?",
            "What would improve this applicant's creditworthiness?",
        ]
        : [
            "What does this project do?",
            "How does prediction work end to end?",
            "What is SHAP used for here?",
            "How does the underwriting form work?",
        ];

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function parseMarkdown(text) {
        const escaped = escapeHtml(String(text || ""));

        function formatInline(line) {
            return line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        }

        const lines = escaped.split("\n");
        const parts = [];
        let inList = false;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const isBullet = /^(\* |- )/.test(line);

            if (isBullet) {
                const itemText = line.replace(/^(\* |- )/, "");
                if (!inList) {
                    parts.push("<ul>");
                    inList = true;
                }
                parts.push(`<li>${formatInline(itemText)}</li>`);
            } else {
                if (inList) {
                    parts.push("</ul>");
                    inList = false;
                }
                parts.push(formatInline(line));
                if (i < lines.length - 1) {
                    parts.push("<br>");
                }
            }
        }

        if (inList) {
            parts.push("</ul>");
        }

        return parts.join("");
    }

    function addMessage(role, text) {
        const msg = document.createElement("div");
        msg.className = `chatbot-message ${role}`;
        if (role === "user") {
            msg.innerHTML = parseMarkdown(text);
        } else {
            msg.textContent = text;
        }
        messagesEl.appendChild(msg);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function createTypingIndicator() {
        const typing = document.createElement("div");
        typing.id = "chatbot-typing-indicator";
        typing.className = "chatbot-message assistant typing";
        typing.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
        messagesEl.appendChild(typing);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function removeTypingIndicator() {
        const existing = document.getElementById("chatbot-typing-indicator");
        if (existing) existing.remove();
    }

    async function addAssistantMessageAnimated(text) {
        const msg = document.createElement("div");
        msg.className = "chatbot-message assistant";
        msg.textContent = "";
        messagesEl.appendChild(msg);

        const content = String(text || "");
        if (!content) {
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return;
        }

        const step = content.length > 500 ? 4 : content.length > 250 ? 3 : 2;
        const delay = content.length > 500 ? 4 : 10;

        await new Promise((resolve) => {
            let index = 0;
            const timer = setInterval(() => {
                index = Math.min(content.length, index + step);
                msg.textContent = content.slice(0, index);
                messagesEl.scrollTop = messagesEl.scrollHeight;
                if (index >= content.length) {
                    clearInterval(timer);
                    resolve();
                }
            }, delay);
        });

        msg.innerHTML = parseMarkdown(content);
        speakAssistantResponse(content);
    }

    async function sendMessage(message) {
        const userText = String(message || "").trim();
        if (!userText) return;

        addMessage("user", userText);
        input.value = "";
        input.disabled = true;
        createTypingIndicator();

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
                removeTypingIndicator();
                await addAssistantMessageAnimated(
                    payload.error || payload.reply || `Unable to answer right now (HTTP ${response.status}).`
                );
            } else {
                removeTypingIndicator();
                await addAssistantMessageAnimated(payload.reply || "No response generated.");
            }
        } catch (error) {
            removeTypingIndicator();
            if (error && error.name === "AbortError") {
                await addAssistantMessageAnimated("The model is taking longer than expected. Please try again in a moment.");
            } else {
                await addAssistantMessageAnimated("Connection error. Please try again.");
            }
        } finally {
            removeTypingIndicator();
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
            ? "Good day. I am reviewing the most recent applicant record evaluated by our underwriting system. How may I assist you?"
            : "Good day. I am the Credit Officer for this institution. Submit a loan application for evaluation, then ask me about the applicant record."
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
        addMessage(
            "assistant",
            pageContext.page === "dashboard"
                ? "Good day. I am reviewing the most recent applicant record evaluated by our underwriting system. How may I assist you?"
                : "Chat reset. Submit a loan application for evaluation, then consult the Credit Officer."
        );
    });

    if (expandToggleBtn) {
        expandToggleBtn.addEventListener("click", () => {
            panel.classList.toggle("expanded");
            const isExpanded = panel.classList.contains("expanded");
            expandToggleBtn.textContent = isExpanded ? "🗗" : "⛶";
            expandToggleBtn.title = isExpanded ? "Collapse chat" : "Expand chat";
        });
    }
});

// ==========================================================================
// Interactive Credit Simulator (Dashboard What-If)
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const simulatorPanel = document.getElementById("credit-simulator-panel");
    if (!simulatorPanel) return;

    const contextNode = document.getElementById("chatbot-context");
    let pageContext = {};
    if (contextNode && contextNode.textContent) {
        try {
            pageContext = JSON.parse(contextNode.textContent);
        } catch (_) {
            return;
        }
    }

    const baseline = pageContext.applicant || {};
    const sliders = {
        creditscore: document.getElementById("sim-creditscore"),
        income: document.getElementById("sim-income"),
        loanamount: document.getElementById("sim-loanamount"),
        dtiratio: document.getElementById("sim-dtiratio"),
        loanterm: document.getElementById("sim-loanterm"),
    };
    const valueLabels = {
        creditscore: document.getElementById("sim-val-creditscore"),
        income: document.getElementById("sim-val-income"),
        loanamount: document.getElementById("sim-val-loanamount"),
        dtiratio: document.getElementById("sim-val-dtiratio"),
        loanterm: document.getElementById("sim-val-loanterm"),
    };
    const resultsPanel = document.getElementById("simulation-results-panel");
    const verdictEl = document.getElementById("simulation-verdict");
    const probabilityEl = document.getElementById("simulation-probability");
    const riskLevelEl = document.getElementById("simulation-risk-level");
    const statusEl = document.getElementById("simulation-status");

    let simulateTimer = null;
    let activeRequest = null;

    function formatCurrency(value) {
        return `$${Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
    }

    function updateSliderLabels() {
        if (valueLabels.creditscore && sliders.creditscore) {
            valueLabels.creditscore.textContent = sliders.creditscore.value;
        }
        if (valueLabels.income && sliders.income) {
            valueLabels.income.textContent = formatCurrency(sliders.income.value);
        }
        if (valueLabels.loanamount && sliders.loanamount) {
            valueLabels.loanamount.textContent = formatCurrency(sliders.loanamount.value);
        }
        if (valueLabels.dtiratio && sliders.dtiratio) {
            valueLabels.dtiratio.textContent = Number(sliders.dtiratio.value).toFixed(2);
        }
        if (valueLabels.loanterm && sliders.loanterm) {
            valueLabels.loanterm.textContent = sliders.loanterm.value;
        }
    }

    function collectOverrides() {
        return {
            creditscore: Number(sliders.creditscore?.value),
            income: Number(sliders.income?.value),
            loanamount: Number(sliders.loanamount?.value),
            dtiratio: Number(sliders.dtiratio?.value),
            loanterm: Number(sliders.loanterm?.value),
        };
    }

    function applyResultsPanelStyle(prediction, riskLevel) {
        if (!resultsPanel) return;

        resultsPanel.classList.remove(
            "simulation-results-panel--approve",
            "simulation-results-panel--reject",
            "simulation-results-panel--medium"
        );

        if (prediction === 0) {
            resultsPanel.classList.add("simulation-results-panel--approve");
        } else if (riskLevel === "Medium Risk") {
            resultsPanel.classList.add("simulation-results-panel--medium");
        } else {
            resultsPanel.classList.add("simulation-results-panel--reject");
        }
    }

    function updateResultsPanel(data) {
        const probability = Number(data.probability);
        const prediction = Number(data.prediction);
        const riskLevel = String(data.risk_level || "");

        if (verdictEl) {
            verdictEl.textContent = `SIMULATED VERDICT: ${prediction === 0 ? "APPROVE" : "REJECT"}`;
        }
        if (probabilityEl) {
            probabilityEl.textContent = `${(probability * 100).toFixed(2)}%`;
        }
        if (riskLevelEl) {
            riskLevelEl.textContent = riskLevel;
        }
        if (statusEl) {
            statusEl.textContent = "Simulation updated";
        }

        applyResultsPanelStyle(prediction, riskLevel);
    }

    async function runSimulation() {
        if (statusEl) statusEl.textContent = "Simulating…";

        if (activeRequest) {
            activeRequest.abort();
        }
        activeRequest = new AbortController();

        try {
            const response = await fetch("/api/predict/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    baseline,
                    overrides: collectOverrides(),
                }),
                signal: activeRequest.signal,
            });

            const payload = await response.json();
            if (!response.ok) {
                if (statusEl) statusEl.textContent = payload.error || "Simulation failed.";
                return;
            }

            updateResultsPanel(payload);
        } catch (error) {
            if (error && error.name === "AbortError") return;
            if (statusEl) statusEl.textContent = "Connection error during simulation.";
        } finally {
            activeRequest = null;
        }
    }

    function scheduleSimulation() {
        updateSliderLabels();
        if (simulateTimer) clearTimeout(simulateTimer);
        simulateTimer = setTimeout(runSimulation, 400);
    }

    Object.values(sliders).forEach((slider) => {
        if (!slider) return;
        slider.addEventListener("input", scheduleSimulation);
        slider.addEventListener("change", scheduleSimulation);
    });

    updateSliderLabels();

    // ==========================================================================
    // Circular Rose (Coxcomb) SVG Wheel for Visual Diagnostics
    // ==========================================================================
    function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
        var angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
        return {
            x: centerX + (radius * Math.cos(angleInRadians)),
            y: centerY + (radius * Math.sin(angleInRadians))
        };
    }

    function getWedgePath(x, y, r_in, r_out, startAngle, endAngle) {
        var start_in = polarToCartesian(x, y, r_in, startAngle);
        var start_out = polarToCartesian(x, y, r_out, startAngle);
        var end_out = polarToCartesian(x, y, r_out, endAngle);
        var end_in = polarToCartesian(x, y, r_in, endAngle);
        
        var largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
        
        return [
            "M", start_out.x, start_out.y,
            "A", r_out, r_out, 0, largeArcFlag, 1, end_out.x, end_out.y,
            "L", end_in.x, end_in.y,
            "A", r_in, r_in, 0, largeArcFlag, 0, start_in.x, start_in.y,
            "Z"
        ].join(" ");
    }

    function initDiagnosticsWheel() {
        const wheelDataEl = document.getElementById("diagnostics-wheel-data");
        if (!wheelDataEl) return;
        
        const factors = JSON.parse(wheelDataEl.getAttribute("data-factors") || "[]");
        const prediction = parseInt(wheelDataEl.getAttribute("data-prediction") || "0");
        const probability = parseFloat(wheelDataEl.getAttribute("data-probability") || "0");
        const riskLevel = wheelDataEl.getAttribute("data-risk-level") || "";
        
        const svg = document.getElementById("diagnostics-wheel");
        const legendContainer = document.getElementById("diagnostics-wheel-legend");
        if (!svg || !legendContainer) return;
        
        svg.innerHTML = "";
        legendContainer.innerHTML = "";
        
        if (factors.length === 0) return;
        
        const N = factors.length;
        const centerX = 150;
        const centerY = 150;
        const r_inner = 55;
        const r_max = 130;
        
        const max_impact = Math.max(...factors.map(f => f.abs), 0.001);
        
        const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        
        const riskGrad = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
        riskGrad.setAttribute("id", "wheel-grad-risk");
        riskGrad.innerHTML = `
            <stop offset="0%" stop-color="#f43f5e" />
            <stop offset="100%" stop-color="#ec4899" />
        `;
        defs.appendChild(riskGrad);
        
        const boostGrad = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
        boostGrad.setAttribute("id", "wheel-grad-boost");
        boostGrad.innerHTML = `
            <stop offset="0%" stop-color="#06b6d4" />
            <stop offset="100%" stop-color="#22d3ee" />
        `;
        defs.appendChild(boostGrad);
        
        svg.appendChild(defs);
        
        function formatParamName(raw) {
            let s = raw.replace(/_/g, ' ');
            if (s.startsWith('Employmenttype ')) return 'Employment: ' + s.substring(15);
            if (s.startsWith('Loanpurpose ')) return 'Purpose: ' + s.substring(12);
            if (s.startsWith('Maritalstatus ')) return 'Marital: ' + s.substring(14);
            if (s.toLowerCase() === 'creditscore band') return 'Credit Score Category';
            if (s.toLowerCase() === 'creditscore') return 'Credit Score';
            if (s.toLowerCase() === 'dtiratio') return 'DTI Ratio';
            if (s.toLowerCase() === 'monthsemployed') return 'Months Employed';
            if (s.toLowerCase() === 'numcreditlines') return 'Credit Lines';
            if (s.toLowerCase() === 'interestrate') return 'Interest Rate';
            if (s.toLowerCase() === 'loanamount') return 'Loan Amount';
            if (s.toLowerCase() === 'loanterm') return 'Loan Term';
            if (s.toLowerCase() === 'log income') return 'Log Income';
            if (s.toLowerCase() === 'log loanamount') return 'Log Loan Amount';
            if (s.toLowerCase() === 'high risk flag') return 'High Risk Flag';
            if (s.toLowerCase() === 'payment to income') return 'Payment-to-Income';
            if (s.toLowerCase() === 'debt burden score') return 'Debt Burden';
            return s;
        }
        
        const centerVerdict = document.getElementById("wheel-center-verdict");
        const centerValue = document.getElementById("wheel-center-value");
        const centerLabel = document.getElementById("wheel-center-label");
        
        function resetCenterText() {
            if (centerVerdict) {
                centerVerdict.textContent = prediction === 0 ? "APPROVED" : "REJECTED";
                centerVerdict.style.color = prediction === 0 ? "#10b981" : "#f43f5e";
            }
            if (centerValue) {
                centerValue.textContent = (probability * 100).toFixed(1) + "%";
            }
            if (centerLabel) {
                centerLabel.textContent = riskLevel;
                centerLabel.style.color = "var(--text-muted)";
            }
        }
        
        resetCenterText();
        
        const angleWidth = 360 / N;
        
        factors.forEach((factor, i) => {
            const startAngle = i * angleWidth;
            const endAngle = (i + 1) * angleWidth;
            const r_out = r_inner + (factor.abs / max_impact) * (r_max - r_inner);
            
            const pathData = getWedgePath(centerX, centerY, r_inner, r_out, startAngle, endAngle);
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathData);
            path.setAttribute("class", `wheel-wedge wedge-${i}`);
            
            const color = factor.direction === 'increased' ? 'url(#wheel-grad-risk)' : 'url(#wheel-grad-boost)';
            const glowColor = factor.direction === 'increased' ? '#f43f5e' : '#22d3ee';
            
            path.setAttribute("fill", color);
            path.style.setProperty("--glow-color", glowColor);
            
            path.addEventListener("mouseenter", () => highlightFactor(i));
            path.addEventListener("mouseleave", () => unhighlightFactor(i));
            
            svg.appendChild(path);
            
            const item = document.createElement("div");
            item.className = `legend-list-item legend-item-${i}`;
            
            const sign = factor.impact >= 0 ? "+" : "";
            const formattedName = formatParamName(factor.param);
            const formattedImpact = `${sign}${factor.impact.toFixed(2)}`;
            
            item.style.setProperty("--hover-border", factor.direction === 'increased' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(34, 211, 238, 0.3)');
            
            item.innerHTML = `
                <div class="legend-item-left">
                    <span class="legend-dot legend-dot--${factor.direction === 'increased' ? 'risk' : 'boost'}"></span>
                    <span>${formattedName}</span>
                </div>
                <span class="legend-badge legend-badge--${factor.direction === 'increased' ? 'risk' : 'boost'}">
                    ${formattedImpact}
                </span>
            `;
            
            item.addEventListener("mouseenter", () => highlightFactor(i));
            item.addEventListener("mouseleave", () => unhighlightFactor(i));
            
            legendContainer.appendChild(item);
        });
        
        function highlightFactor(idx) {
            const wedge = svg.querySelector(`.wedge-${idx}`);
            if (wedge) wedge.classList.add("active");
            
            const legendItem = legendContainer.querySelector(`.legend-item-${idx}`);
            if (legendItem) legendItem.classList.add("active");
            
            const f = factors[idx];
            const formattedName = formatParamName(f.param);
            const sign = f.impact >= 0 ? "+" : "";
            
            if (centerVerdict) {
                centerVerdict.textContent = f.direction === 'increased' ? "RISK FACTOR" : "CREDIT BOOST";
                centerVerdict.style.color = f.direction === 'increased' ? "#fda4af" : "#67e8f9";
            }
            if (centerValue) {
                centerValue.textContent = `${sign}${f.impact.toFixed(2)}`;
            }
            if (centerLabel) {
                centerLabel.textContent = formattedName;
                centerLabel.style.color = "var(--text-primary)";
            }
        }
        
        function unhighlightFactor(idx) {
            const wedge = svg.querySelector(`.wedge-${idx}`);
            if (wedge) wedge.classList.remove("active");
            
            const legendItem = legendContainer.querySelector(`.legend-item-${idx}`);
            if (legendItem) legendItem.classList.remove("active");
            
            resetCenterText();
        }
    }

    initDiagnosticsWheel();
});
