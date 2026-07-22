/**
 * Theme Module
 * 
 * Dark/light mode toggle with localStorage persistence
 * and system preference detection.
 */

(function () {
    // Load saved theme or detect system preference
    const saved = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (systemDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', theme);

    // Update highlight.js theme if present
    updateHljsTheme(theme);
})();

/**
 * Toggle between dark and light themes.
 */
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);

    // Update theme switch visual
    const themeSwitch = document.getElementById('themeSwitch');
    if (themeSwitch) {
        themeSwitch.classList.toggle('active', next === 'dark');
    }

    // Update highlight.js theme
    updateHljsTheme(next);
}

/**
 * Update highlight.js stylesheet based on theme.
 */
function updateHljsTheme(theme) {
    const link = document.getElementById('hljs-theme');
    if (link) {
        link.href = theme === 'dark'
            ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css'
            : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
    }
}

/**
 * Initialize theme toggle on the dashboard.
 */
function initTheme() {
    const themeSwitch = document.getElementById('themeSwitch');
    if (themeSwitch) {
        const current = document.documentElement.getAttribute('data-theme');
        themeSwitch.classList.toggle('active', current === 'dark');
        themeSwitch.addEventListener('click', toggleTheme);
    }
}
