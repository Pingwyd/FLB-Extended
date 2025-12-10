// Check for dark mode preference immediately to prevent FOUC
try {
    const user = JSON.parse(localStorage.getItem('flb_user') || '{}');
    const userId = user.id;
    const themeKey = userId ? `theme_${userId}` : 'theme';
    
    if (localStorage.getItem(themeKey) === 'dark' || (!localStorage.getItem(themeKey) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
} catch (e) {
    console.error('Error parsing user for theme', e);
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
}
