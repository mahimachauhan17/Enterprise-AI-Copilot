/**
 * Dashboard Module
 * 
 * Initializes all dashboard modules and handles
 * top-level coordination on page load.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auth check
    if (!checkAuth()) return;

    // Load user profile
    loadUserProfile();

    // Initialize all modules
    initTheme();
    initChat();
    initUpload();
    initSidebar();
    initSettings();
    initSearch();
    initProfileDropdown();

    // Load initial data
    loadChatHistory();
    loadDocuments();
});

/**
 * Load user profile data from localStorage.
 */
function loadUserProfile() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const profileAvatar = document.getElementById('profileAvatar');
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');

    if (profileAvatar) {
        profileAvatar.textContent = (user.username || 'U').charAt(0).toUpperCase();
    }
    if (profileName) {
        profileName.textContent = user.username || 'User';
    }
    if (profileEmail) {
        profileEmail.textContent = user.email || '';
    }
}

/**
 * Initialize profile dropdown.
 */
function initProfileDropdown() {
    const profileBtn = document.getElementById('profileBtn');
    const profileMenu = document.getElementById('profileMenu');
    const logoutBtn = document.getElementById('logoutBtn');

    // Guard: these elements may not exist in the current layout
    if (!profileBtn || !profileMenu) return;

    // Toggle dropdown
    profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profileMenu.classList.toggle('active');
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.profile-dropdown')) {
            profileMenu.classList.remove('active');
        }
    });

    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}
