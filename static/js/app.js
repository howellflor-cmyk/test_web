// Global CSRF token for fetch requests
const getCSRFToken = () => {
    return document.querySelector('meta[name="csrf-token"]')?.content || 
           window.csrfToken || 
           document.body.dataset.csrfToken || '';
};

// Intercept all fetch requests to add CSRF token
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const [resource, config = {}] = args;
    
    // Add CSRF token to POST/PUT/DELETE requests
    if (config.method && ['POST', 'PUT', 'DELETE'].includes(config.method)) {
        if (!config.headers) config.headers = {};
        config.headers['X-CSRFToken'] = getCSRFToken();
    }
    
    return originalFetch.apply(this, args);
};

// Auto-dismiss flash messages after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash-message');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    });
});