document.addEventListener('alpine:init', () => {
    Alpine.data('layout', () => ({
        mobileMenuOpen: false,
        isLoggedIn: localStorage.getItem('is_logged_in') === 'true',
        user: JSON.parse(localStorage.getItem('flb_user') || '{}'),
        
        logout() {
            localStorage.removeItem('is_logged_in');
            localStorage.removeItem('flb_user');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_email');
            this.isLoggedIn = false;
            window.location.href = '/';
        }
    }));
});

// Page Transition Logic
document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('main-content');
    
    document.body.addEventListener('click', (e) => {
        // Find the closest anchor tag
        const link = e.target.closest('a');
        if (!link) return;
        
        const href = link.getAttribute('href');
        const target = link.getAttribute('target');
        
        // Ignore special links
        if (!href || 
            href.startsWith('#') || 
            href.startsWith('javascript:') || 
            href.startsWith('mailto:') ||
            href.startsWith('tel:') ||
            target === '_blank' || 
            e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
            return;
        }

        // Check if it's an internal link
        try {
            const url = new URL(href, window.location.origin);
            if (url.origin !== window.location.origin) return;
        } catch (err) {
            // If URL parsing fails, it might be a relative path, which is fine
        }

        // Prevent default navigation
        e.preventDefault();

        // Add exit animation class
        if (mainContent) {
            mainContent.classList.remove('page-enter');
            mainContent.classList.add('page-exit');
        }

        // Wait for animation then navigate
        setTimeout(() => {
            window.location.href = href;
        }, 300); // Match the 0.3s animation duration in style.css
    });

    // Handle Back/Forward Cache (BFCache)
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            if (mainContent) {
                mainContent.classList.remove('page-exit');
                mainContent.classList.add('page-enter');
            }
        }
    });
});
