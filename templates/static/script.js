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

    // Initial check for local storage or system preference
    const storedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
        setDarkMode(true);
    } else {
        setDarkMode(false);
    }

    // Add a change event listener to the toggle checkbox
    themeToggle.addEventListener('change', (event) => {
        setDarkMode(event.target.checked);
    });
});
