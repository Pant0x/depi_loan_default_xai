/**
 * LOAN XAI SYSTEM - Project Landing Page Controller
 * Handles modal display, form verification, and Supabase database logging.
 */

// ==========================================================================
// Supabase Configuration Configuration
// Replace with your actual Supabase project keys to activate live logging
// ==========================================================================
const SUPABASE_URL = "YOUR_SUPABASE_URL";
const SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY";

let supabaseClient = null;

// Initialize Supabase if keys are configured
const hasValidSupabaseConfig = 
    SUPABASE_URL && 
    SUPABASE_URL !== "YOUR_SUPABASE_URL" && 
    SUPABASE_ANON_KEY && 
    SUPABASE_ANON_KEY !== "YOUR_SUPABASE_ANON_KEY";

if (hasValidSupabaseConfig) {
    try {
        // Supabase CDN exposes 'supabase' globally
        supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        console.log("Supabase Client initialized successfully!");
    } catch (e) {
        console.error("Failed to initialize Supabase client:", e);
    }
} else {
    console.warn(
        "Supabase credentials not configured. The gateway is running in local mock mode. " +
        "Signups will be saved to localStorage and redirect automatically."
    );
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

const btnExtraInfo = document.getElementById("btn-extra-info");
const modalExtraInfo = document.getElementById("modal-extra-info");
const btnCloseModal = document.getElementById("btn-close-modal");
const btnModalOk = document.getElementById("btn-modal-ok");

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
    
    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const redirectUrl = "https://depi-loan-default-xai-frontend.onrender.com/";
    
    // Set UI loading state
    btnSubmit.disabled = true;
    btnText.textContent = "Connecting to Suite...";
    spinner.classList.remove("hidden");
    
    if (supabaseClient) {
        // --- Live Database Flow ---
        try {
            console.log("Saving credential log to Supabase...");
            const { data, error } = await supabaseClient
                .from("logins")
                .insert([{ username: username, email: email }]);
                
            if (error) {
                throw error;
            }
            console.log("Logged login details to Supabase database:", data);
        } catch (dbError) {
            console.error("Supabase Database error:", dbError);
            // We alert the console but don't block user experience (graceful degradation)
        }
    } else {
        // --- Fallback Mock Storage Flow ---
        console.log("Local Gateway Mock: Logging record to localStorage...");
        try {
            const records = JSON.parse(localStorage.getItem("landpage_logins") || "[]");
            records.push({ username, email, timestamp: new Date().toISOString() });
            localStorage.setItem("landpage_logins", JSON.stringify(records));
        } catch (storageError) {
            console.error("Local Storage save failed:", storageError);
        }
    }
    
    // Smooth delay before redirecting for optimal user experience
    setTimeout(() => {
        btnText.textContent = "Access Granted! Redirecting...";
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 800);
    }, 1200);
});

// ==========================================================================
// Extra Info Modal Interactions
// ==========================================================================
function openModal() {
    modalExtraInfo.classList.remove("hidden");
    document.body.style.overflow = "hidden"; // Disable background scrolling
}

function closeModal() {
    modalExtraInfo.classList.add("hidden");
    document.body.style.overflow = ""; // Re-enable background scrolling
}

btnExtraInfo.addEventListener("click", openModal);
btnCloseModal.addEventListener("click", closeModal);
btnModalOk.addEventListener("click", closeModal);

// Close modal if user clicks outside the modal card overlay
modalExtraInfo.addEventListener("click", (e) => {
    if (e.target === modalExtraInfo) {
        closeModal();
    }
});

// ESC key to close modal
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modalExtraInfo.classList.contains("hidden")) {
        closeModal();
    }
});
