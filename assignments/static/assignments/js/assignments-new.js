/**
 * Assignments App - Core functionality
 * Wrapped in initialization function for SPA compatibility
 */

function initializeAssignmentsPage() {
    // Guard: Only run if we're on assignments page
    if (!document.querySelector('#assignmentsContainer')) return;

    // Prevent double initialization
    if (window.assignmentsInitialized) return;
    window.assignmentsInitialized = true;

    function loadEmployeeFilter() {
        fetch('/employees/api/employees/')
            .then(response => response.json())
            .then(data => {
                const employeeFilter = document.getElementById('employeeFilter');
                if (employeeFilter) {
                    data.results.forEach(employee => {
                        const option = document.createElement('option');
                        option.value = employee.id;
                        option.textContent = `${employee.first_name} ${employee.last_name}`;
                        employeeFilter.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading employee filter:', error);
            });
    }

    // Assignment-specific functions
    function showReturnModal(deviceId) {
        // Load return device modal content via HTMX
        const modalContent = document.getElementById('return-modal-content');
        htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
            target: '#return-modal-content',
            swap: 'innerHTML'
        });

        const modal = new bootstrap.Modal(document.getElementById('returnModal'));
        modal.show();
    }

    function refreshAssignments() {
        // Trigger HTMX refresh
        htmx.trigger(document.body, 'refreshAssignments');
    }

    function exportAssignments() {
        // Get current filter values
        const form = document.getElementById('filterForm');
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        params.append('export', 'csv');

        window.open(`/assignments/api/assignments/?${params.toString()}`, '_blank');
    }

    // Global alert function
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const alertContainer = document.getElementById('alert-container') || document.querySelector('main');
        alertContainer.insertBefore(alertDiv, alertContainer.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Filter form submission
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const params = new URLSearchParams(formData);

            // Update assignments list with filters
            htmx.ajax('GET', `/assignments/api/assignments/?${params.toString()}`, {
                target: '#assignmentsContainer',
                swap: 'innerHTML'
            });
        });
    }

    // HTMX integration
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.elt.id === 'assignmentsContainer') {
            console.log('Assignments list refreshed');
        }
    });

    // Initialize on page load
    loadEmployeeFilter();

    // Function to open assign device modal (for header button)
    function openAssignDeviceModal() {
        // Load assign device modal via HTMX
        htmx.ajax('GET', '/assignments/assign/', {
            target: '#dynamicModalContent',
            swap: 'innerHTML'
        }).then(() => {
            // Show the modal after content is loaded
            const modalEl = document.getElementById('dynamicModal');
            if (modalEl) {
                // Get or create modal instance
                let modal = bootstrap.Modal.getInstance(modalEl);
                if (!modal) {
                    modal = new bootstrap.Modal(modalEl);
                }
                modal.show();
            } else {
                console.error('dynamicModal element not found');
            }
        });
    }

    // Make functions globally available
    window.showReturnModal = showReturnModal;
    window.refreshAssignments = refreshAssignments;
    window.exportAssignments = exportAssignments;
    window.showAlert = showAlert;
    window.openAssignDeviceModal = openAssignDeviceModal;
}

// Export initialization function
window.initializeAssignmentsPage = initializeAssignmentsPage;

// Auto-initialize on direct page load (non-HTMX)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAssignmentsPage);
} else {
    initializeAssignmentsPage();
}
