/**
 * LOAN XAI SYSTEM - Project Landing Page Controller
 * Handles form verification, Supabase database logging, and toast notifications.
 */

// ==========================================================================
// Supabase Configuration
// ==========================================================================
const SUPABASE_URL = "https://nceokvawdzxwjzqitszd.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jZW9rdmF3ZHp4d2p6cWl0c3pkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMzM3MjYsImV4cCI6MjA5NzcwOTcyNn0.fNqf3Lq8MkpAwFW3yRFJ2jhHgar1NeDXZ1eLnjYOIJo";

let supabaseClient = null;

// Initialize Supabase client
const hasValidSupabaseConfig = 
    SUPABASE_URL && 
    SUPABASE_URL !== "YOUR_SUPABASE_URL" && 
    SUPABASE_ANON_KEY && 
    SUPABASE_ANON_KEY !== "YOUR_SUPABASE_ANON_KEY";

if (hasValidSupabaseConfig) {
    try {
        supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        console.log("Supabase Client initialized successfully.");
    } catch (e) {
        console.error("Failed to initialize Supabase client:", e);
    }
} else {
    console.warn(
        "Supabase credentials not configured. Running in local mock mode. " +
        "Signups will be saved to localStorage and redirect automatically."
    );
}

// ==========================================================================
// Toast Notification System
// ==========================================================================
function showToast(message, type = "info", duration = 4000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

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

// ==========================================================================
// Input Sanitization
// ==========================================================================
function sanitizeInput(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML.trim();
}

// ==========================================================================
// Rate Limiting (localStorage-based, 1 submission per 30 seconds)
// ==========================================================================
function isRateLimited() {
    const lastSubmit = localStorage.getItem("last_login_submit");
    if (!lastSubmit) return false;
    const elapsed = Date.now() - parseInt(lastSubmit, 10);
    return elapsed < 30000; // 30 seconds cooldown
}

function markSubmission() {
    localStorage.setItem("last_login_submit", Date.now().toString());
}

// ==========================================================================
// Document Elements Selection
// ==========================================================================
const loginForm = document.getElementById("login-form");
const usernameInput = document.getElementById("username");
const emailInput = document.getElementById("email");
const btnSubmit = document.getElementById("btn-submit");
const btnText = btnSubmit.querySelector(".btn-text");
const spinner = btnSubmit.querySelector(".spinner");

// ==========================================================================
// Form Validation Logic
// ==========================================================================
function validateForm() {
    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    // Enable button only if both inputs are non-empty and email format is valid
    if (username.length >= 3 && emailRegex.test(email)) {
        btnSubmit.disabled = false;
    } else {
        btnSubmit.disabled = true;
    }
}

// Attach input listeners for live validation
usernameInput.addEventListener("input", validateForm);
emailInput.addEventListener("input", validateForm);

// ==========================================================================
// Form Submission & Supabase Storage
// ==========================================================================
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Rate limit check
    if (isRateLimited()) {
        showToast("Please wait a moment before submitting again.", "warning");
        return;
    }

    const username = sanitizeInput(usernameInput.value);
    const email = sanitizeInput(emailInput.value);
    const redirectUrl = "https://depi-loan-default-xai-frontend.onrender.com/";
    
    // Validate sanitized values
    if (username.length < 3 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showToast("Please enter valid credentials.", "error");
        return;
    }

    // Set UI loading state
    btnSubmit.disabled = true;
    btnText.textContent = "Connecting to Suite...";
    spinner.classList.remove("hidden");
    
    if (supabaseClient) {
        // --- Live Database Flow ---
        try {
            const { data, error } = await supabaseClient
                .from("logins")
                .insert([{ username: username, email: email }]);
                
            if (error) {
                throw error;
            }
            console.log("User credentials logged to Supabase.");
        } catch (dbError) {
            console.error("Supabase Database error:", dbError);
            // Graceful degradation — don't block the user
            showToast("Connection logged locally (database temporarily unavailable).", "warning");
            // Fallback to localStorage
            try {
                const records = JSON.parse(localStorage.getItem("landpage_logins") || "[]");
                records.push({ username, email, timestamp: new Date().toISOString() });
                localStorage.setItem("landpage_logins", JSON.stringify(records));
            } catch (storageError) {
                // Silent fail
            }
        }
    } else {
        // --- Fallback Mock Storage Flow ---
        console.log("Local mode: Logging record to localStorage.");
        try {
            const records = JSON.parse(localStorage.getItem("landpage_logins") || "[]");
            records.push({ username, email, timestamp: new Date().toISOString() });
            localStorage.setItem("landpage_logins", JSON.stringify(records));
        } catch (storageError) {
            console.error("Local Storage save failed:", storageError);
        }
    }
    
    // Mark rate limiter
    markSubmission();

    // Smooth delay before redirecting
    setTimeout(() => {
        btnText.textContent = "Access Granted! Redirecting...";
        showToast("Access granted. Redirecting to LOAN XAI SYSTEM...", "success");
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 800);
    }, 1200);
});
