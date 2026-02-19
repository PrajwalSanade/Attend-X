// ============================================
// DARK/LIGHT MODE THEME TOGGLE
// ============================================
// Handles theme switching with localStorage persistence
// ============================================

// Theme configuration
const THEME_KEY = 'attend_x_theme';
const THEME_LIGHT = 'light';
const THEME_DARK = 'dark';

// ============================================
// THEME FUNCTIONS
// ============================================

/**
 * Get current theme from localStorage or system preference
 * @returns {string} 'light' or 'dark'
 */
function getCurrentTheme() {
    // Check localStorage first
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme) {
        return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return THEME_DARK;
    }
    
    // Default to light
    return THEME_LIGHT;
}

/**
 * Apply theme to document
 * @param {string} theme - 'light' or 'dark'
 */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    
    console.log(`🎨 Theme changed to: ${theme}`);
    
    // Dispatch custom event for other scripts to listen
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
    applyTheme(newTheme);
}

/**
 * Create theme toggle button
 */
function createThemeToggle() {
    // Check if toggle already exists
    if (document.querySelector('.theme-toggle')) {
        return;
    }
    
    // Create toggle button
    const toggle = document.createElement('button');
    toggle.className = 'theme-toggle';
    toggle.setAttribute('aria-label', 'Toggle theme');
    toggle.setAttribute('title', 'Toggle dark/light mode');
    
    // Add icons
    toggle.innerHTML = `
        <svg class="theme-toggle-icon sun-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg class="theme-toggle-icon moon-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
    `;
    
    // Add click handler
    toggle.addEventListener('click', toggleTheme);
    
    // Add to body
    document.body.appendChild(toggle);
    
    console.log('✅ Theme toggle button created');
}

/**
 * Initialize theme system
 */
function initializeTheme() {
    // Apply saved or default theme
    const theme = getCurrentTheme();
    applyTheme(theme);
    
    // Create toggle button
    createThemeToggle();
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem(THEME_KEY)) {
                const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
                applyTheme(newTheme);
            }
        });
    }
    
    console.log('✅ Theme system initialized');
}

// ============================================
// KEYBOARD SHORTCUT
// ============================================

// Add keyboard shortcut: Ctrl/Cmd + Shift + T
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        toggleTheme();
    }
});

// ============================================
// INITIALIZATION
// ============================================

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
} else {
    initializeTheme();
}

// Export functions for use in other scripts
window.themeManager = {
    getCurrentTheme,
    applyTheme,
    toggleTheme,
    THEME_LIGHT,
    THEME_DARK
};

console.log('✅ Theme module loaded');
console.log('💡 Tip: Press Ctrl+Shift+T to toggle theme');
