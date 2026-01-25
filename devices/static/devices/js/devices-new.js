/**
 * Devices App - Enhanced with Bulk Operations Framework
 * Wrapped in initialization function for SPA compatibility
 * Version: 2025-10-25-modal-fix - Return device modal standardized to dynamicModal
 */

// Global variables accessible across all functions (use var to allow redeclaration across page scripts)
var bulkManager;
var currentDeviceId = null;

// Critical functions defined globally so they're always available
function showAssignModal(deviceId) {
    currentDeviceId = deviceId;

    // Load assign device modal with preselected device via HTMX
    htmx.ajax('GET', `/assignments/assign/${deviceId}/`, {
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

function showUnassignModal(deviceId) {
    currentDeviceId = deviceId;

    // Verify modal exists before proceeding
    const modalEl = document.getElementById('dynamicModal');
    if (!modalEl) {
        console.error('dynamicModal element not found in DOM');
        console.log('Available modals:', document.querySelectorAll('.modal'));
        showAlert('Modal container not found. Please refresh the page.', 'danger');
        return;
    }

    // Load return device modal content via HTMX using standardized dynamicModal
    htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
        target: '#dynamicModalContent',
        swap: 'innerHTML'
    }).then(() => {
        // Get modal instance after content is loaded
        let modal = bootstrap.Modal.getInstance(modalEl);
        if (!modal) {
            modal = new bootstrap.Modal(modalEl);
        }
        modal.show();
    }).catch(error => {
        console.error('Error loading return device modal:', error);
        showAlert('Failed to load return device form. Please try again.', 'danger');
    });
}

function showEditModal(deviceId) {
    currentDeviceId = deviceId;

    // Verify modal exists before proceeding
    const modalEl = document.getElementById('dynamicModal');
    if (!modalEl) {
        console.error('dynamicModal element not found in DOM');
        showAlert('Modal container not found. Please refresh the page.', 'danger');
        return;
    }

    // Load edit device modal content via HTMX
    htmx.ajax('GET', `/devices/${deviceId}/edit/`, {
        target: '#dynamicModalContent',
        swap: 'innerHTML'
    }).then(() => {
        // Get modal instance after content is loaded
        let modal = bootstrap.Modal.getInstance(modalEl);
        if (!modal) {
            modal = new bootstrap.Modal(modalEl);
        }
        modal.show();
    }).catch(error => {
        console.error('Error loading edit device modal:', error);
        showAlert('Failed to load edit device form. Please try again.', 'danger');
    });
}

function exportDevices() {
    window.open('/devices/search/?export=csv', '_blank');
}

function refreshDeviceList() {
    htmx.ajax('GET', '/devices/api/devices/', {
        target: '#devices-table',
        swap: 'innerHTML'
    });
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('main').insertBefore(alertDiv, document.querySelector('main').firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function toggleBulkMode() {
    if (bulkManager) {
        bulkManager.toggleBulkMode();
    }
}

// Export functions immediately so they're always available
window.showAssignModal = showAssignModal;
window.showUnassignModal = showUnassignModal;
window.showEditModal = showEditModal;
window.exportDevices = exportDevices;
window.refreshDeviceList = refreshDeviceList;
window.showAlert = showAlert;
window.toggleBulkMode = toggleBulkMode;

function initializeDevicesPage() {
    // Guard: Only run if we're on devices page
    if (!document.querySelector('#devices-table')) {
        console.warn('Devices table not found, skipping initialization');
        return;
    }

    // Prevent double initialization
    if (window.devicesInitialized) {
        console.log('Devices already initialized, skipping');
        return;
    }
    window.devicesInitialized = true;
    console.log('Starting devices initialization...');

    let bulkManager;
    let currentDeviceId = null;

    function initializeBulkOperations() {
        // Configuration for device bulk operations
        const bulkConfig = {
            tableSelector: '#devices-table',
            apiEndpoint: '/devices/api/bulk-operations/',
            bulkButtonId: 'bulkActionsBtn',
            modalId: 'bulkOperationsModal',
            selectAllId: 'selectAllDevices',
            checkboxClass: 'device-checkbox',
            bulkCellClass: 'bulk-select-cell',
            bulkHeaderId: 'bulk-select-header',

            // Device-specific operations with enhanced permissions
            operations: {
                update_status: {
                    label: 'Update Status',
                    icon: 'bi bi-gear',
                    permission: 'can_modify_devices',
                    fields: [
                        {
                            name: 'new_status',
                            type: 'select',
                            label: 'New Status',
                            required: true,
                            options: [
                                { value: 'available', label: 'Available' },
                                { value: 'retired', label: 'Retired' },
                                { value: 'lost', label: 'Lost/Stolen' },
                                { value: 'damaged', label: 'Damaged' }
                            ]
                        }
                    ]
                },

                update_location: {
                    label: 'Update Location',
                    icon: 'bi bi-geo-alt',
                    permission: 'can_modify_devices',
                    fields: [
                        {
                            name: 'new_location',
                            type: 'select',
                            label: 'New Location',
                            required: true
                        }
                    ],
                    loadData: function() {
                        loadLocationsForBulk();
                    }
                },

                update_specifications: {
                    label: 'Update Specifications',
                    icon: 'bi bi-cpu',
                    permission: 'can_modify_devices',
                    fields: [
                        {
                            name: 'spec_updates',
                            type: 'textarea',
                            label: 'Specification Updates',
                            required: true,
                            rows: 4,
                            placeholder: 'Enter JSON format: {"RAM": "16GB", "Storage": "512GB SSD"}',
                            helpText: 'JSON format to merge with existing specifications'
                        }
                    ]
                },

                assign_devices: {
                    label: 'Assign to Employee',
                    icon: 'bi bi-person-plus',
                    permission: 'can_assign_devices',
                    fields: [
                        {
                            name: 'employee_id',
                            type: 'select',
                            label: 'Assign to Employee',
                            required: true
                        },
                        {
                            name: 'expected_return_date',
                            type: 'date',
                            label: 'Expected Return Date',
                            required: false
                        },
                        {
                            name: 'notes',
                            type: 'textarea',
                            label: 'Assignment Notes',
                            required: false,
                            rows: 3
                        }
                    ],
                    loadData: function() {
                        loadEmployeesForBulkAssign();
                    }
                },

                unassign_devices: {
                    label: 'Unassign Devices',
                    icon: 'bi bi-person-dash',
                    permission: 'can_assign_devices',
                    fields: [
                        {
                            name: 'condition',
                            type: 'select',
                            label: 'Return Condition',
                            required: false,
                            options: [
                                { value: '', label: 'Keep current condition' },
                                { value: 'new', label: 'New' },
                                { value: 'excellent', label: 'Excellent' },
                                { value: 'good', label: 'Good' },
                                { value: 'fair', label: 'Fair' },
                                { value: 'poor', label: 'Poor' }
                            ]
                        },
                        {
                            name: 'notes',
                            type: 'textarea',
                            label: 'Return Notes',
                            required: false,
                            rows: 3,
                            placeholder: 'Return notes...'
                        }
                    ]
                }
            },

            // Permission checks - these would be populated from Django template context
            permissions: {
                can_modify_devices: window.userPermissions?.can_modify_devices || false,
                can_assign_devices: window.userPermissions?.can_assign_devices || false
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
                refreshDeviceList();
            }
        };

        // Initialize the bulk operations manager
        bulkManager = new BulkOperationsManager(bulkConfig);

        // Make it globally available
        window.bulkManager = bulkManager;
    }

    // Enhanced data loading functions
    function loadLocationsForBulk() {
        fetch('/devices/api/locations/')
            .then(response => response.json())
            .then(data => {
                const locationSelect = document.querySelector('select[name="new_location"]');
                if (locationSelect) {
                    locationSelect.innerHTML = '<option value="">Select location...</option>';
                    data.forEach(location => {
                        locationSelect.innerHTML += `<option value="${location.name}">${location.name}</option>`;
                    });
                }
            })
            .catch(() => {
                const locationSelect = document.querySelector('select[name="new_location"]');
                if (locationSelect) {
                    locationSelect.innerHTML = '<option value="">Error loading locations</option>';
                }
            });
    }

    function loadEmployeesForBulkAssign() {
        fetch('/employees/api/employees/')
            .then(response => response.json())
            .then(data => {
                const employeeSelect = document.querySelector('select[name="employee_id"]');
                if (employeeSelect) {
                    employeeSelect.innerHTML = '<option value="">Choose an employee...</option>';
                    data.results.forEach(employee => {
                        employeeSelect.innerHTML += `<option value="${employee.id}">${employee.first_name} ${employee.last_name} - ${employee.department || 'No Dept'}</option>`;
                    });
                }
            })
            .catch(() => {
                const employeeSelect = document.querySelector('select[name="employee_id"]');
                if (employeeSelect) {
                    employeeSelect.innerHTML = '<option value="">Error loading employees</option>';
                }
            });
    }

    // Legacy functions for backward compatibility (just wrappers now)
    function showBulkOperationsModal() {
        if (bulkManager) {
            bulkManager.showOperationsModal();
        }
    }

    function showBulkForm(operation) {
        if (bulkManager) {
            bulkManager.showOperationForm(operation);
        }
    }

    function backToBulkMenu() {
        if (bulkManager) {
            bulkManager.backToOperationsMenu();
        }
    }

    function executeBulkOperation() {
        if (bulkManager) {
            bulkManager.executeOperation();
        }
    }

    // Enable bulk actions button after page loads
    function enableBulkActionsButton() {
        const bulkBtn = document.getElementById('bulkActionsBtn');
        if (bulkBtn) {
            bulkBtn.disabled = false;
        }
    }

    // HTMX integration
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.elt.id === 'devices-table') {
            console.log('Devices table refreshed');
            // Re-initialize bulk operations after HTMX updates
            if (bulkManager) {
                bulkManager.init();
            }
        }
    });

    // Initialize on page load
    initializeBulkOperations();
    enableBulkActionsButton();

    console.log('Devices page initialization complete');
}

// Export initialization function
window.initializeDevicesPage = initializeDevicesPage;

// Auto-initialize on direct page load (non-HTMX)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDevicesPage);
} else {
    initializeDevicesPage();
}
