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
        document.body.addEventListener('htmx:configRequest', (event) => {
            const csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                event.detail.headers['X-CSRFToken'] = csrfToken;
            }
        });
        
        // Sidebar toggle functionality (both mobile and desktop)
        document.addEventListener('DOMContentLoaded', function() {
            const sidebarToggleBtn = document.querySelector('.sidebar-toggle-btn');
            const sidebar = document.getElementById('sidebarMenu');
            const mainContent = document.querySelector('.main-content');

            // Only proceed if sidebar exists (authenticated users only)
            if (!sidebar || !sidebarToggleBtn || !mainContent) {
                return;
            }

            // Load sidebar state from localStorage (desktop only)
            if (window.innerWidth >= 768) {
                const sidebarHidden = localStorage.getItem('sidebarHidden') === 'true';
                if (sidebarHidden) {
                    sidebar.classList.add('sidebar-hidden');
                    mainContent.classList.add('sidebar-hidden');
                }
            }

            // Toggle sidebar visibility
            sidebarToggleBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();

                // Desktop: Hide/show sidebar
                if (window.innerWidth >= 768) {
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

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', function(event) {
                if (window.innerWidth < 768 && sidebar) {
                    const isToggleButton = event.target.closest('.sidebar-toggle-btn');
                    const isSidebar = event.target.closest('#sidebarMenu');

                    if (!isToggleButton && !isSidebar && sidebar.classList.contains('mobile-show')) {
                        sidebar.classList.remove('mobile-show');
                        document.body.classList.remove('mobile-sidebar-open');
                    }
                }
            });

            // Logout button now uses direct form submission (no JavaScript needed)
            // The form in sidebar.html handles logout via POST with CSRF token

            // Update navbar active state on HTMX navigation
            function updateNavbarActiveState() {
                // Get current path, keep root as '/', remove trailing slash from others
                let currentPath = window.location.pathname;
                if (currentPath !== '/' && currentPath.endsWith('/')) {
                    currentPath = currentPath.slice(0, -1);
                }

                const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

                // First, remove all active classes
                navLinks.forEach(link => link.classList.remove('active'));

                // Build array of links with normalized paths
                const linkData = Array.from(navLinks).map(link => {
                    const href = link.getAttribute('href');
                    if (!href) return null;

                    // Normalize link path the same way
                    let linkPath = href;
                    if (linkPath !== '/' && linkPath.endsWith('/')) {
                        linkPath = linkPath.slice(0, -1);
                    }

                    return { link, linkPath };
                }).filter(item => item !== null);

                // PHASE 1: Look for EXACT match first (highest priority)
                const exactMatch = linkData.find(item => item.linkPath === currentPath);

                if (exactMatch) {
                    // Found exact match - use it and we're done
                    exactMatch.link.classList.add('active');
                } else {
                    // PHASE 2: No exact match - look for longest prefix match (for sub-pages)
                    // Sort by path length (longest first) to find most specific prefix
                    linkData.sort((a, b) => b.linkPath.length - a.linkPath.length);

                    for (const item of linkData) {
                        const { link, linkPath } = item;

                        // Skip root path in prefix matching
                        if (linkPath === '/') continue;

                        // Check if current path starts with this link path followed by '/'
                        // This handles sub-pages like /devices/123/ matching /devices
                        if (currentPath.startsWith(linkPath + '/')) {
                            link.classList.add('active');
                            break; // Found best prefix match, stop looking
                        }
                    }

                    // PHASE 3: Fallback for root path
                    if (currentPath === '/') {
                        const dashboardLink = linkData.find(item => item.linkPath === '/');
                        if (dashboardLink) {
                            dashboardLink.link.classList.add('active');
                        }
                    }
                }
            }

            // Update on ANY HTMX content swap (not just content-area)
            document.body.addEventListener('htmx:afterSwap', function(event) {
                updateNavbarActiveState();
            });

            // Update on HTMX settle as well for reliability
            document.body.addEventListener('htmx:afterSettle', function(event) {
                updateNavbarActiveState();
            });

            // Update on browser back/forward
            document.body.addEventListener('htmx:historyRestore', function() {
                updateNavbarActiveState();
            });

            // Update on popstate (browser navigation)
            window.addEventListener('popstate', function() {
                setTimeout(updateNavbarActiveState, 50);
            });

            // Initial call on page load - with small delay for DOM readiness
            updateNavbarActiveState();
            setTimeout(updateNavbarActiveState, 100);
        });