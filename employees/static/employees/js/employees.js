/**
 * Employees App - Core functionality
 * Wrapped in initialization function for SPA compatibility
 */

function initializeEmployeesPage() {
    // Guard: Only run if we're on employees page
    if (!document.querySelector('#employees-table')) return;

    // Prevent double initialization
    if (window.employeesInitialized) return;
    window.employeesInitialized = true;

    function setupFilterHandlers() {
        // Handle search and filter inputs
        const searchInput = document.querySelector('input[name="search"]');
        const departmentSelect = document.querySelector('select[name="department"]');
        const statusSelect = document.querySelector('select[name="status"]');

        // Add event listeners for manual filter handling
        [searchInput, departmentSelect, statusSelect].forEach(element => {
            if (element) {
                element.addEventListener('change', function() {
                    // HTMX will handle the actual filtering
                    console.log('Filter changed:', element.name, element.value);
                });
            }
        });
    }

    // Employee-specific functions
    function exportEmployees() {
        // Get current filter values
        const searchValue = document.querySelector('input[name="search"]')?.value || '';
        const departmentValue = document.querySelector('select[name="department"]')?.value || '';
        const statusValue = document.querySelector('select[name="status"]')?.value || '';

        const params = new URLSearchParams();
        if (searchValue) params.append('search', searchValue);
        if (departmentValue) params.append('department', departmentValue);
        if (statusValue) params.append('status', statusValue);
        params.append('export', 'csv');

        window.open(`/employees/api/employees/?${params.toString()}`, '_blank');
    }

    function refreshEmployeeList() {
        // Trigger HTMX refresh for the employee table
        htmx.ajax('GET', '/employees/api/employees/', {
            target: '#employees-table',
            swap: 'innerHTML'
        });
    }

    // Global alert function
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const main = document.querySelector('main') || document.body;
        main.insertBefore(alertDiv, main.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Initialize on page load
    setupFilterHandlers();

    // Make functions globally available
    window.exportEmployees = exportEmployees;
    window.refreshEmployeeList = refreshEmployeeList;
    window.showAlert = showAlert;
}

// Export initialization function
window.initializeEmployeesPage = initializeEmployeesPage;

// Auto-initialize on direct page load (non-HTMX)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEmployeesPage);
} else {
    initializeEmployeesPage();
}
