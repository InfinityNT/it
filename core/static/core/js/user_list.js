/**
 * User Management - Enhanced with Bulk Operations Framework
 */

let bulkManager;

// Initialize bulk operations when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeBulkOperations();
    enableBulkActionsButton();
});

function initializeBulkOperations() {
    // Configuration for user bulk operations
    const bulkConfig = {
        tableSelector: '#users-table',
        apiEndpoint: '/api/users/bulk-operations/',
        bulkButtonId: 'bulkActionsBtn',
        modalId: 'bulkOperationsModal',
        selectAllId: 'selectAllUsers',
        checkboxClass: 'user-checkbox',
        bulkCellClass: 'bulk-select-cell',
        bulkHeaderId: 'bulk-select-header',
        
        // User-specific operations with permissions
        operations: {
            activate_users: {
                label: 'Activate Users',
                icon: 'bi bi-check-circle',
                permission: 'can_manage_users',
                description: 'Activate selected inactive user accounts',
                fields: []
            },
            
            deactivate_users: {
                label: 'Deactivate Users',
                icon: 'bi bi-x-circle',
                permission: 'can_manage_users',
                description: 'Deactivate selected active user accounts',
                fields: []
            },
            
            assign_group: {
                label: 'Assign to User Group',
                icon: 'bi bi-people',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'new_group_id',
                        type: 'select',
                        label: 'Assign to Group',
                        required: true
                    },
                    {
                        name: 'replace_existing',
                        type: 'checkbox',
                        label: 'Replace Existing Groups',
                        value: true,
                        helpText: 'Remove users from all other groups first'
                    }
                ],
                loadData: function() {
                    loadUserGroupsForBulk();
                }
            },
            
            remove_from_group: {
                label: 'Remove from User Group',
                icon: 'bi bi-person-dash',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'group_id',
                        type: 'select',
                        label: 'Remove from Group',
                        required: true
                    }
                ],
                loadData: function() {
                    loadUserGroupsForBulk();
                }
            },
            
            force_password_change: {
                label: 'Force Password Change',
                icon: 'bi bi-key',
                permission: 'can_manage_system',
                description: 'Require users to change their password on next login',
                fields: []
            },
            
            reset_passwords: {
                label: 'Reset Passwords',
                icon: 'bi bi-shield-lock',
                permission: 'can_manage_system',
                description: 'Generate new temporary passwords for selected users',
                fields: [],
                confirmationText: 'Are you sure you want to reset passwords for the selected users? New temporary passwords will be generated and users will be required to change them on next login.'
            },
            
            update_staff_status: {
                label: 'Update Staff Status',
                icon: 'bi bi-person-gear',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'is_staff',
                        type: 'select',
                        label: 'Staff Status',
                        required: true,
                        options: [
                            { value: true, label: 'Grant Staff Access' },
                            { value: false, label: 'Remove Staff Access' }
                        ]
                    }
                ]
            },
            
            export_users: {
                label: 'Export Selected Users',
                icon: 'bi bi-download',
                permission: 'can_view_users',
                description: 'Export selected user data to various formats',
                fields: [
                    {
                        name: 'export_format',
                        type: 'select',
                        label: 'Export Format',
                        required: true,
                        options: [
                            { value: 'csv', label: 'CSV (Comma Separated Values)' },
                            { value: 'pdf', label: 'PDF Report' },
                            { value: 'json', label: 'JSON Data' }
                        ]
                    },
                    {
                        name: 'include_permissions',
                        type: 'checkbox',
                        label: 'Include Permission Details',
                        value: true,
                        helpText: 'Include user permissions and capabilities'
                    },
                    {
                        name: 'include_groups',
                        type: 'checkbox',
                        label: 'Include Group Memberships',
                        value: true,
                        helpText: 'Include user group assignments'
                    }
                ]
            }
        },
        
        // Permission checks
        permissions: {
            can_manage_users: window.userPermissions?.can_manage_users || false,
            can_view_users: window.userPermissions?.can_view_users || false,
            can_manage_system: window.userPermissions?.can_manage_system || false
        },
        
        // Custom callbacks
        onSuccess: function(data) {
            let message = data.message || 'Bulk operation completed successfully';
            
            // Special handling for password reset results
            if (data.reset_results && data.reset_results.length > 0) {
                let passwordTable = '<br><br><strong>New Temporary Passwords:</strong><br><table class="table table-sm table-bordered mt-2"><thead><tr><th>User</th><th>Username</th><th>Temporary Password</th></tr></thead><tbody>';
                data.reset_results.forEach(result => {
                    passwordTable += `<tr><td>${result.user}</td><td><code>${result.username}</code></td><td><code>${result.temp_password}</code></td></tr>`;
                });
                passwordTable += '</tbody></table><small class="text-muted">Users will be required to change passwords on next login.</small>';
                message += passwordTable;
            }
            
            if (data.errors && data.errors.length > 0) {
                message += `\n\nWarnings:\n${data.errors.join('\n')}`;
            }
            showAlert('success', message);
        },
        
        onError: function(errorMessage) {
            showAlert('danger', errorMessage);
        },
        
        onRefresh: function() {
            refreshUsersList();
        }
    };
    
    // Initialize the bulk operations manager
    bulkManager = new BulkOperationsManager(bulkConfig);
    
    // Make it globally available
    window.bulkManager = bulkManager;
}

// Enhanced data loading functions
function loadUserGroupsForBulk() {
    fetch('/core/api/groups/')
        .then(response => response.json())
        .then(data => {
            const groupSelects = document.querySelectorAll('select[name="new_group_id"], select[name="group_id"]');
            groupSelects.forEach(select => {
                select.innerHTML = '<option value="">Choose group...</option>';
                data.forEach(group => {
                    select.innerHTML += `<option value="${group.id}">${group.name}</option>`;
                });
            });
        })
        .catch(() => {
            const groupSelects = document.querySelectorAll('select[name="new_group_id"], select[name="group_id"]');
            groupSelects.forEach(select => {
                select.innerHTML = '<option value="">Error loading groups</option>';
            });
        });
}

// Legacy functions for backward compatibility and individual user actions
function toggleBulkMode() {
    bulkManager.toggleBulkMode();
}

function showBulkOperationsModal() {
    bulkManager.showOperationsModal();
}

function toggleUserStatus(userId, action) {
    const actionText = action === 'activate' ? 'activate' : 'deactivate';
    if (!confirm(`Are you sure you want to ${actionText} this user?`)) {
        return;
    }
    
    fetch(`/api/users/${userId}/toggle-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showAlert('success', data.message);
            refreshUsersList();
        } else {
            showAlert('danger', data.error || `Failed to ${actionText} user`);
        }
    })
    .catch(error => {
        showAlert('danger', `An error occurred while trying to ${actionText} the user`);
    });
}

function resetUserPassword(userId, userName) {
    if (!confirm(`Are you sure you want to reset the password for ${userName}?\n\nThis will generate a new temporary password and require the user to change it on next login.`)) {
        return;
    }
    
    fetch(`/api/users/${userId}/reset-password/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showAlert('success', `${data.message}<br><strong>Temporary Password:</strong> <code>${data.temporary_password}</code><br><small>${data.note}</small>`);
        } else {
            showAlert('danger', data.error || 'Failed to reset password');
        }
    })
    .catch(error => {
        showAlert('danger', 'An error occurred while resetting the password');
    });
}

function refreshUsersList() {
    // Trigger HTMX refresh for the users table
    htmx.ajax('GET', '/api/users/', {
        target: '#users-table',
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
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('main').insertBefore(alertDiv, document.querySelector('main').firstChild);
    
    // Auto-remove after appropriate timeout (longer for password info)
    const timeout = type === 'success' && message.includes('Temporary Password') ? 15000 : 5000;
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, timeout);
}

// CSRF token helper
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

// Make functions globally available
window.toggleUserStatus = toggleUserStatus;
window.resetUserPassword = resetUserPassword;
window.refreshUsersList = refreshUsersList;
window.showAlert = showAlert;
window.toggleBulkMode = toggleBulkMode;

// HTMX integration
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.elt.id === 'users-table') {
        console.log('Users table refreshed');
        // Re-initialize bulk operations after HTMX updates
        if (bulkManager) {
            bulkManager.init();
        }
    }
});