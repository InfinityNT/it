/**
 * Employees App - Enhanced with Bulk Operations Framework
 * Wrapped in initialization function for SPA compatibility
 */

function initializeEmployeesPage() {
    // Guard: Only run if we're on employees page
    if (!document.querySelector('#employees-table')) return;

    // Prevent double initialization
    if (window.employeesInitialized) return;
    window.employeesInitialized = true;

    let bulkManager;
    
    // Initialize bulk operations when page loads
    document.addEventListener('DOMContentLoaded', function() {
        initializeBulkOperations();
        enableBulkActionsButton();
        setupFilterHandlers();
    });
    
    function initializeBulkOperations() {
        // Configuration for employee bulk operations
        const bulkConfig = {
            tableSelector: '#employees-table',
            apiEndpoint: '/employees/api/bulk-operations/',
            bulkButtonId: 'bulkActionsBtn',
            modalId: 'bulkOperationsModal',
            selectAllId: 'selectAllEmployees',
            checkboxClass: 'employee-checkbox',
            bulkCellClass: 'bulk-select-cell',
            bulkHeaderId: 'bulk-select-header',
            
            // Employee-specific operations with permissions
            operations: {
                update_status: {
                    label: 'Update Employment Status',
                    icon: 'bi bi-person-gear',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'new_employment_status',
                            type: 'select',
                            label: 'New Employment Status',
                            required: true,
                            options: [
                                { value: 'active', label: 'Active' },
                                { value: 'inactive', label: 'Inactive' },
                                { value: 'on_leave', label: 'On Leave' },
                                { value: 'terminated', label: 'Terminated' }
                            ]
                        },
                        {
                            name: 'status_reason',
                            type: 'textarea',
                            label: 'Reason for Status Change',
                            required: false,
                            rows: 3,
                            placeholder: 'Optional reason for status change...'
                        }
                    ]
                },
                
                bulk_department_transfer: {
                    label: 'Department Transfer',
                    icon: 'bi bi-building',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'new_department_id',
                            type: 'select',
                            label: 'Transfer to Department',
                            required: true
                        },
                        {
                            name: 'new_job_title_id',
                            type: 'select',
                            label: 'New Job Title',
                            required: false
                        },
                        {
                            name: 'transfer_date',
                            type: 'date',
                            label: 'Transfer Effective Date',
                            required: false,
                            helpText: 'Leave blank for immediate transfer'
                        },
                        {
                            name: 'transfer_reason',
                            type: 'textarea',
                            label: 'Transfer Reason',
                            required: false,
                            rows: 3,
                            placeholder: 'Reason for department transfer...'
                        }
                    ],
                    loadData: function() {
                        loadDepartmentsAndJobTitles();
                    }
                },
                
                update_location: {
                    label: 'Update Office Location',
                    icon: 'bi bi-geo-alt',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'new_office_location',
                            type: 'select',
                            label: 'New Office Location',
                            required: true
                        },
                        {
                            name: 'new_building',
                            type: 'text',
                            label: 'Building',
                            required: false,
                            placeholder: 'Building name/number'
                        },
                        {
                            name: 'new_floor',
                            type: 'text',
                            label: 'Floor',
                            required: false,
                            placeholder: 'Floor number'
                        },
                        {
                            name: 'new_desk_number',
                            type: 'text',
                            label: 'Desk Number',
                            required: false,
                            placeholder: 'Desk/office number'
                        }
                    ],
                    loadData: function() {
                        loadLocationsForBulk();
                    }
                },
                
                update_contact_info: {
                    label: 'Update Contact Information',
                    icon: 'bi bi-telephone',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'new_work_phone',
                            type: 'tel',
                            label: 'Work Phone',
                            required: false,
                            placeholder: '+1 (555) 123-4567'
                        },
                        {
                            name: 'new_mobile_phone',
                            type: 'tel',
                            label: 'Mobile Phone',
                            required: false,
                            placeholder: '+1 (555) 123-4567'
                        },
                        {
                            name: 'new_work_email',
                            type: 'email',
                            label: 'Work Email',
                            required: false,
                            placeholder: 'employee@company.com'
                        },
                        {
                            name: 'contact_update_reason',
                            type: 'textarea',
                            label: 'Update Reason',
                            required: false,
                            rows: 2,
                            placeholder: 'Reason for contact information update...'
                        }
                    ]
                },
                
                assign_manager: {
                    label: 'Assign Manager',
                    icon: 'bi bi-person-lines-fill',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'new_manager_id',
                            type: 'select',
                            label: 'Assign Manager',
                            required: true
                        },
                        {
                            name: 'manager_assignment_date',
                            type: 'date',
                            label: 'Effective Date',
                            required: false,
                            helpText: 'Leave blank for immediate assignment'
                        },
                        {
                            name: 'manager_assignment_notes',
                            type: 'textarea',
                            label: 'Assignment Notes',
                            required: false,
                            rows: 2,
                            placeholder: 'Notes about manager assignment...'
                        }
                    ],
                    loadData: function() {
                        loadManagersForBulk();
                    }
                },
                
                update_access_level: {
                    label: 'Update System Access',
                    icon: 'bi bi-shield-check',
                    permission: 'can_manage_system',
                    fields: [
                        {
                            name: 'system_access_action',
                            type: 'select',
                            label: 'System Access Action',
                            required: true,
                            options: [
                                { value: 'grant', label: 'Grant System Access' },
                                { value: 'revoke', label: 'Revoke System Access' },
                                { value: 'update_groups', label: 'Update User Groups' }
                            ]
                        },
                        {
                            name: 'user_groups',
                            type: 'select',
                            label: 'User Groups',
                            required: false,
                            helpText: 'Only applies when granting access or updating groups'
                        },
                        {
                            name: 'access_reason',
                            type: 'textarea',
                            label: 'Access Change Reason',
                            required: true,
                            rows: 3,
                            placeholder: 'Required: Justification for access level changes...'
                        }
                    ],
                    loadData: function() {
                        loadUserGroupsForBulk();
                    }
                },
                
                add_notes: {
                    label: 'Add Notes to Employee Records',
                    icon: 'bi bi-chat-text',
                    permission: 'can_modify_employees',
                    fields: [
                        {
                            name: 'note_category',
                            type: 'select',
                            label: 'Note Category',
                            required: true,
                            options: [
                                { value: 'general', label: 'General Note' },
                                { value: 'performance', label: 'Performance Note' },
                                { value: 'administrative', label: 'Administrative Note' },
                                { value: 'hr', label: 'HR Note' },
                                { value: 'it', label: 'IT Note' }
                            ]
                        },
                        {
                            name: 'note_content',
                            type: 'textarea',
                            label: 'Note Content',
                            required: true,
                            rows: 4,
                            placeholder: 'Enter note content...'
                        }
                    ]
                }
            },
            
            // Permission checks
            permissions: {
                can_modify_employees: window.userPermissions?.can_modify_employees || false,
                can_view_employees: window.userPermissions?.can_view_employees || false,
                can_manage_system: window.userPermissions?.can_manage_system || false
            },
            
            // Custom callbacks
            onSuccess: function(data) {
                let message = data.message || 'Bulk operation completed successfully';
                if (data.errors && data.errors.length > 0) {
                    message += `\\n\\nWarnings:\\n${data.errors.join('\\n')}`;
                }
                showAlert('success', message);
            },
            
            onError: function(errorMessage) {
                showAlert('danger', errorMessage);
            },
            
            onRefresh: function() {
                refreshEmployeeList();
            }
        };
        
        // Initialize the bulk operations manager
        bulkManager = new BulkOperationsManager(bulkConfig);
        
        // Make it globally available
        window.bulkManager = bulkManager;
    }
    
    // Enhanced data loading functions
    function loadDepartmentsAndJobTitles() {
        // Load departments
        fetch('/employees/api/departments/')
            .then(response => response.json())
            .then(data => {
                const deptSelect = document.querySelector('select[name="new_department_id"]');
                if (deptSelect) {
                    deptSelect.innerHTML = '<option value="">Choose department...</option>';
                    data.forEach(dept => {
                        deptSelect.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
                    });
                }
            })
            .catch(() => {
                const deptSelect = document.querySelector('select[name="new_department_id"]');
                if (deptSelect) {
                    deptSelect.innerHTML = '<option value="">Error loading departments</option>';
                }
            });
    
        // Load job titles
        fetch('/employees/api/job-titles/')
            .then(response => response.json())
            .then(data => {
                const titleSelect = document.querySelector('select[name="new_job_title_id"]');
                if (titleSelect) {
                    titleSelect.innerHTML = '<option value="">Keep current title</option>';
                    data.forEach(title => {
                        titleSelect.innerHTML += `<option value="${title.id}">${title.title}</option>`;
                    });
                }
            })
            .catch(() => {
                const titleSelect = document.querySelector('select[name="new_job_title_id"]');
                if (titleSelect) {
                    titleSelect.innerHTML = '<option value="">Error loading job titles</option>';
                }
            });
    }
    
    function loadLocationsForBulk() {
        fetch('/devices/api/locations/')
            .then(response => response.json())
            .then(data => {
                const locationSelect = document.querySelector('select[name="new_office_location"]');
                if (locationSelect) {
                    locationSelect.innerHTML = '<option value="">Choose location...</option>';
                    data.forEach(location => {
                        locationSelect.innerHTML += `<option value="${location.name}">${location.name}</option>`;
                    });
                }
            })
            .catch(() => {
                const locationSelect = document.querySelector('select[name="new_office_location"]');
                if (locationSelect) {
                    locationSelect.innerHTML = '<option value="">Error loading locations</option>';
                }
            });
    }
    
    function loadManagersForBulk() {
        fetch('/employees/api/employees/?role=manager')
            .then(response => response.json())
            .then(data => {
                const managerSelect = document.querySelector('select[name="new_manager_id"]');
                if (managerSelect) {
                    managerSelect.innerHTML = '<option value="">Choose manager...</option>';
                    data.results.forEach(employee => {
                        managerSelect.innerHTML += `<option value="${employee.id}">${employee.first_name} ${employee.last_name} - ${employee.job_title || 'No Title'}</option>`;
                    });
                }
            })
            .catch(() => {
                const managerSelect = document.querySelector('select[name="new_manager_id"]');
                if (managerSelect) {
                    managerSelect.innerHTML = '<option value="">Error loading managers</option>';
                }
            });
    }
    
    function loadUserGroupsForBulk() {
        fetch('/core/api/groups/')
            .then(response => response.json())
            .then(data => {
                const groupSelect = document.querySelector('select[name="user_groups"]');
                if (groupSelect) {
                    groupSelect.innerHTML = '<option value="">Choose user group...</option>';
                    data.forEach(group => {
                        groupSelect.innerHTML += `<option value="${group.id}">${group.name}</option>`;
                    });
                }
            })
            .catch(() => {
                const groupSelect = document.querySelector('select[name="user_groups"]');
                if (groupSelect) {
                    groupSelect.innerHTML = '<option value="">Error loading user groups</option>';
                }
            });
    }
    
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
    
    // Legacy functions for backward compatibility
    function toggleBulkMode() {
        bulkManager.toggleBulkMode();
    }
    
    function showBulkOperationsModal() {
        bulkManager.showOperationsModal();
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
        
        const main = document.querySelector('main') || document.body;
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Make functions globally available

    // Initialize on page load
    initializeBulkOperations();
    enableBulkActionsButton();
    setupFilterHandlers();

    // Make functions globally available
    window.exportEmployees = exportEmployees;
    window.refreshEmployeeList = refreshEmployeeList;
    window.showAlert = showAlert;
    window.toggleBulkMode = toggleBulkMode;
}

// Export initialization function
window.initializeEmployeesPage = initializeEmployeesPage;

// Auto-initialize on direct page load (non-HTMX)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEmployeesPage);
} else {
    initializeEmployeesPage();
}
