// ==========================================
// Core Application JavaScript
// Handles: CSRF, sidebar toggle, toasts, modals, HTMX errors
// ==========================================

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Setup CSRF token for HTMX requests
document.addEventListener('htmx:configRequest', (event) => {
    const csrfToken = getCookie('dmp_csrftoken');
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

// ==========================================
// Sidebar Toggle Functionality
// ==========================================
(function() {
    // Apply saved sidebar state on page load
    function applySavedSidebarState() {
        const sidebar = document.getElementById('sidebarMenu');
        const mainContent = document.querySelector('.main-content');

        if (!sidebar || !mainContent) return;

        if (window.innerWidth >= 1143) {
            const sidebarHidden = localStorage.getItem('sidebarHidden') === 'true';
            if (sidebarHidden) {
                sidebar.classList.add('sidebar-hidden');
                mainContent.classList.add('sidebar-hidden');
            }
        }
    }

    // Close button inside sidebar drawer
    document.addEventListener('click', function(event) {
        const closeBtn = event.target.closest('.sidebar-close-btn');
        if (!closeBtn) return;

        event.preventDefault();
        event.stopPropagation();

        const sidebar = document.getElementById('sidebarMenu');
        if (sidebar) {
            sidebar.classList.remove('mobile-show');
            document.body.classList.remove('mobile-sidebar-open');
        }
    });

    // Event delegation for sidebar toggle click
    document.addEventListener('click', function(event) {
        const toggleBtn = event.target.closest('.sidebar-toggle-btn');
        if (!toggleBtn) return;

        event.preventDefault();
        event.stopPropagation();

        const sidebar = document.getElementById('sidebarMenu');
        const mainContent = document.querySelector('.main-content');

        if (!sidebar || !mainContent) return;

        // Desktop: Hide/show sidebar
        if (window.innerWidth >= 1143) {
            const isHidden = sidebar.classList.toggle('sidebar-hidden');
            mainContent.classList.toggle('sidebar-hidden');
            localStorage.setItem('sidebarHidden', isHidden);
        }
        // Mobile: Slide sidebar in/out
        else {
            sidebar.classList.toggle('mobile-show');
            document.body.classList.toggle('mobile-sidebar-open');
        }
    });

    // Close sidebar when clicking outside on mobile/tablet
    document.addEventListener('click', function(event) {
        if (window.innerWidth >= 1143) return;

        const sidebar = document.getElementById('sidebarMenu');
        if (!sidebar || !sidebar.classList.contains('mobile-show')) return;

        const isToggleButton = event.target.closest('.sidebar-toggle-btn');
        const isSidebar = event.target.closest('#sidebarMenu');

        if (!isToggleButton && !isSidebar) {
            sidebar.classList.remove('mobile-show');
            document.body.classList.remove('mobile-sidebar-open');
        }
    });

    // Apply saved state on page load
    document.addEventListener('DOMContentLoaded', applySavedSidebarState);
})();

// ==========================================
// Dashboard Navbar Scroll Effect
// ==========================================
(function() {
    function handleNavbarScroll() {
        const navbar = document.getElementById('mainNavbar');
        if (navbar && document.body.classList.contains('dashboard-active')) {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        window.addEventListener('scroll', handleNavbarScroll, { passive: true });
    });
})();

// ==========================================
// Quick Actions Sidebar Refresh
// ==========================================
function refreshQuickActionsSidebar() {
    const quickActionsSection = document.getElementById('quick-actions-section');
    if (quickActionsSection && typeof htmx !== 'undefined') {
        htmx.trigger(quickActionsSection, 'load');
        return true;
    }
    return false;
}

// ==========================================
// HTMX Error Handling
// ==========================================
document.body.addEventListener('htmx:responseError', function(event) {
    console.error('HTMX Response Error:', event.detail);

    const xhr = event.detail.xhr;
    const verb = event.detail.requestConfig?.verb?.toLowerCase();

    // Try to get error message from JSON response
    let errorMessage = 'An error occurred. Please try again.';
    try {
        const response = JSON.parse(xhr.responseText);
        errorMessage = response.error || response.detail || errorMessage;
    } catch (e) {
        if (xhr.status === 403) errorMessage = 'Permission denied.';
        else if (xhr.status === 404) errorMessage = 'Resource not found.';
        else if (xhr.status >= 500) errorMessage = 'Server error. Please try again.';
    }

    // Only replace content for GET requests (not POST/PUT/DELETE actions)
    if (verb === 'get') {
        const target = event.detail.target;
        if (target) {
            target.innerHTML = `
                <div class="error-state text-center py-5">
                    <div class="error-state-icon mb-3">
                        <i class="bi bi-exclamation-triangle display-1 text-danger"></i>
                    </div>
                    <h3 class="error-state-title text-dark mb-2">Failed to load content</h3>
                    <p class="error-state-message text-muted mb-4">
                        We couldn't load this content. This might be a network issue.
                    </p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-1"></i>
                        Reload Page
                    </button>
                </div>
            `;
        }
    }

    showToast('error', errorMessage);
});

document.body.addEventListener('htmx:sendError', function(event) {
    console.error('HTMX Send Error:', event.detail);
    showToast('error', 'Network error. Please check your connection.');
});

document.body.addEventListener('htmx:timeout', function(event) {
    console.warn('HTMX Timeout:', event.detail);
    showToast('warning', 'Request timed out. Please try again.');
});

// ==========================================
// Toast Notification System
// ==========================================
function showToast(type, message, duration = 5000) {
    // Remove existing toasts
    const existingToast = document.querySelector('.custom-toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: min(300px, calc(100vw - 40px));
        max-width: min(500px, calc(100vw - 40px));
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease-out;
    `;

    const iconMap = {
        'success': 'check-circle-fill',
        'error': 'exclamation-triangle-fill',
        'danger': 'exclamation-triangle-fill',
        'warning': 'exclamation-circle-fill',
        'info': 'info-circle-fill'
    };

    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${iconMap[type] || 'info-circle-fill'} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// Add CSS animation for toast
if (!document.getElementById('toast-animation-style')) {
    const style = document.createElement('style');
    style.id = 'toast-animation-style';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

// ==========================================
// Modal Focus Management
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    // Move focus before modal hides to prevent aria-hidden warning
    document.addEventListener('hide.bs.modal', function(event) {
        const modal = event.target;
        const focusedElement = document.activeElement;

        if (modal.contains(focusedElement)) {
            const trigger = document.querySelector(`[data-bs-target="#${modal.id}"]`);
            if (trigger) {
                trigger.focus();
            } else {
                focusedElement.blur();
            }
        }
    });

    // Reset dynamic modal content after hidden
    document.addEventListener('hidden.bs.modal', function(event) {
        if (event.target.id === 'dynamicModal') {
            const modalContent = document.getElementById('dynamicModalContent');
            if (modalContent) {
                modalContent.innerHTML = `
                    <div class="modal-body text-center p-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
            }
        }
    });
});
