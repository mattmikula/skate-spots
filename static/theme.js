document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const select = document.getElementById('theme-select');
    if (!select || !body) {
        return;
    }

    const storageKey = 'skate-spots-theme';
    const defaultTheme = body.dataset.defaultTheme || 'theme-sunset';

    const themeClasses = new Set();

    const refreshThemeClasses = () => {
        themeClasses.clear();
        body.classList.forEach((className) => {
            if (className.startsWith('theme-')) {
                themeClasses.add(className);
            }
        });
        if (themeClasses.size === 0) {
            themeClasses.add(defaultTheme);
            body.classList.add(defaultTheme);
        }
    };

    const applyTheme = (themeName) => {
        refreshThemeClasses();
        themeClasses.forEach((className) => {
            if (className !== themeName) {
                body.classList.remove(className);
            }
        });
        body.classList.add(themeName);
        select.value = themeName;
    };

    refreshThemeClasses();

    const storedTheme = localStorage.getItem(storageKey);
    if (storedTheme && storedTheme !== select.value) {
        applyTheme(storedTheme);
    } else {
        select.value = Array.from(themeClasses)[0];
    }

    select.addEventListener('change', (event) => {
        const selectedTheme = event.target.value;
        if (!selectedTheme.startsWith('theme-')) {
            return;
        }
        applyTheme(selectedTheme);
        localStorage.setItem(storageKey, selectedTheme);
    });
});
