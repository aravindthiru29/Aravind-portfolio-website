/**
 * Theme Toggle — Light (default) / Dark
 * Persists preference in localStorage.
 * Applies theme BEFORE first paint (via inline script in <head>).
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'portfolio-theme';
    const DARK = 'dark';
    const LIGHT = 'light';

    /**
     * Apply theme to <html> element.
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
    }

    /**
     * Get stored theme, falling back to 'light'.
     */
    function getStoredTheme() {
        return localStorage.getItem(STORAGE_KEY) || LIGHT;
    }

    /**
     * Toggle between light and dark.
     */
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || LIGHT;
        const next = current === LIGHT ? DARK : LIGHT;
        applyTheme(next);
    }

    // Apply immediately (in case script loads before DOMContentLoaded)
    applyTheme(getStoredTheme());

    // Bind toggle buttons once DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
        // Re-apply in case the inline <head> script didn't run
        applyTheme(getStoredTheme());

        // Bind every element with class "theme-toggle"
        var toggles = document.querySelectorAll('.theme-toggle');
        toggles.forEach(function (btn) {
            btn.addEventListener('click', toggleTheme);
        });
    });
})();
