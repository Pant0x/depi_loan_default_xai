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
