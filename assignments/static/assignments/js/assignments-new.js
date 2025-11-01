/**
 * Assignments App - Enhanced with Bulk Operations Framework
 * Wrapped in initialization function for SPA compatibility
 */

function initializeAssignmentsPage() {
    // Guard: Only run if we're on assignments page
    if (!document.querySelector('#assignmentsContainer')) return;

    // Prevent double initialization
    if (window.assignmentsInitialized) return;
    window.assignmentsInitialized = true;

    let bulkManager;

    function initializeBulkOperations() {
        // Configuration for assignment bulk operations
        const bulkConfig = {
            tableSelector: '#assignmentsContainer',
            apiEndpoint: '/assignments/api/bulk-operations/',
            bulkButtonId: 'bulkActionsBtn',
            modalId: 'bulkOperationsModal',
            selectAllId: 'selectAllAssignments',
            checkboxClass: 'assignment-checkbox',
            bulkCellClass: 'bulk-select-cell',
            bulkHeaderId: 'bulk-select-header',

            // Assignment-specific operations with permissions
            operations: {
                bulk_return: {
                    label: 'Return Devices',
                    icon: 'bi bi-arrow-return-left',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'return_condition',
                            type: 'select',
                            label: 'Return Condition',
                            required: true,
                            options: [
                                { value: 'new', label: 'New' },
                                { value: 'excellent', label: 'Excellent' },
                                { value: 'good', label: 'Good' },
                                { value: 'fair', label: 'Fair' },
                                { value: 'poor', label: 'Poor' },
                                { value: 'damaged', label: 'Damaged' }
                            ]
                        },
                        {
                            name: 'return_notes',
                            type: 'textarea',
                            label: 'Return Notes',
                            required: false,
                            rows: 3,
                            placeholder: 'Optional notes about device return...'
                        }
                    ]
                },

                update_status: {
                    label: 'Update Assignment Status',
                    icon: 'bi bi-gear',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'new_status',
                            type: 'select',
                            label: 'New Status',
                            required: true,
                            options: [
                                { value: 'active', label: 'Active' },
                                { value: 'returned', label: 'Returned' },
                                { value: 'overdue', label: 'Overdue' }
                            ]
                        },
                        {
                            name: 'status_notes',
                            type: 'textarea',
                            label: 'Status Change Notes',
                            required: false,
                            rows: 2,
                            placeholder: 'Optional notes about status change...'
                        }
                    ]
                },

                extend_return_date: {
                    label: 'Extend Return Dates',
                    icon: 'bi bi-calendar-plus',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'new_expected_return_date',
                            type: 'date',
                            label: 'New Expected Return Date',
                            required: true,
                            helpText: 'Update the expected return date for selected assignments'
                        },
                        {
                            name: 'extension_reason',
                            type: 'textarea',
                            label: 'Extension Reason',
                            required: false,
                            rows: 3,
                            placeholder: 'Reason for extending return date...'
                        }
                    ]
                },

                transfer_assignments: {
                    label: 'Transfer to Another Employee',
                    icon: 'bi bi-person-plus-fill',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'new_employee_id',
                            type: 'select',
                            label: 'Transfer to Employee',
                            required: true
                        },
                        {
                            name: 'transfer_notes',
                            type: 'textarea',
                            label: 'Transfer Notes',
                            required: false,
                            rows: 3,
                            placeholder: 'Reason for transfer, handover instructions...'
                        },
                        {
                            name: 'new_expected_return_date',
                            type: 'date',
                            label: 'New Expected Return Date',
                            required: false,
                            helpText: 'Leave blank to keep current dates'
                        }
                    ],
                    loadData: function() {
                        loadEmployeesForBulkTransfer();
                    }
                },

                mark_overdue: {
                    label: 'Mark as Overdue',
                    icon: 'bi bi-exclamation-triangle',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'overdue_notes',
                            type: 'textarea',
                            label: 'Overdue Notes',
                            required: false,
                            rows: 3,
                            placeholder: 'Notes about why assignments are overdue...'
                        }
                    ]
                },

                add_notes: {
                    label: 'Add Notes to Assignments',
                    icon: 'bi bi-chat-text',
                    permission: 'can_modify_assignments',
                    fields: [
                        {
                            name: 'additional_notes',
                            type: 'textarea',
                            label: 'Additional Notes',
                            required: true,
                            rows: 4,
                            placeholder: 'Notes to add to selected assignments...'
                        }
                    ]
                }
            },

            // Permission checks
            permissions: {
                can_modify_assignments: window.userPermissions?.can_modify_assignments || false,
                can_view_assignments: window.userPermissions?.can_view_assignments || false
            },

            // Custom callbacks
            onSuccess: function(data) {
                let message = data.message || 'Bulk operation completed successfully';
                if (data.errors && data.errors.length > 0) {
                    message += `\n\nWarnings:\n${data.errors.join('\n')}`;
                }
                showAlert('success', message);
            },

            onError: function(errorMessage) {
                showAlert('danger', errorMessage);
            },

            onRefresh: function() {
                refreshAssignments();
            }
        };

        // Initialize the bulk operations manager
        bulkManager = new BulkOperationsManager(bulkConfig);

        // Make it globally available
        window.bulkManager = bulkManager;
    }

    // Enhanced data loading functions
    function loadEmployeesForBulkTransfer() {
        fetch('/employees/api/employees/')
            .then(response => response.json())
            .then(data => {
                const employeeSelect = document.querySelector('select[name="new_employee_id"]');
                if (employeeSelect) {
                    employeeSelect.innerHTML = '<option value="">Choose an employee...</option>';
                    data.results.forEach(employee => {
                        employeeSelect.innerHTML += `<option value="${employee.id}">${employee.first_name} ${employee.last_name} - ${employee.department || 'No Dept'}</option>`;
                    });
                }
            })
            .catch(() => {
                const employeeSelect = document.querySelector('select[name="new_employee_id"]');
                if (employeeSelect) {
                    employeeSelect.innerHTML = '<option value="">Error loading employees</option>';
                }
            });
    }

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

    // Legacy functions for backward compatibility
    function toggleBulkMode() {
        bulkManager.toggleBulkMode();
    }

    function showBulkOperationsModal() {
        bulkManager.showOperationsModal();
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

    // Enable bulk actions button after page loads
    function enableBulkActionsButton() {
        const bulkBtn = document.getElementById('bulkActionsBtn');
        if (bulkBtn) {
            bulkBtn.disabled = false;
        }
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
            // Re-initialize bulk operations after HTMX updates
            if (bulkManager) {
                bulkManager.init();
            }
        }
    });

    // Initialize on page load
    initializeBulkOperations();
    enableBulkActionsButton();
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
    window.toggleBulkMode = toggleBulkMode;
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
