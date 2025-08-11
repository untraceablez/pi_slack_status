// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    const setDarkMode = (isDark) => {
        if (isDark) {
            htmlElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            themeToggle.checked = true;
        } else {
            htmlElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            themeToggle.checked = false;
        }
    };

    // Initial check: Prioritize the user's last choice from local storage.
    // If no choice exists, use the system's preference.
    const storedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Determine the initial state of the dark mode.
    const initialDark = storedTheme === 'dark' || (!storedTheme && prefersDark);
    setDarkMode(initialDark);

    // Add a change event listener to the toggle checkbox.
    // This is the most reliable way to detect user interaction with the toggle.
    themeToggle.addEventListener('change', (event) => {
        setDarkMode(event.target.checked);
    });
});
