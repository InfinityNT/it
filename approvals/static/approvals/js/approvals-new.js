/**
 * Approvals App - Enhanced with Bulk Operations Framework
 */

// Use var to allow redeclaration across page scripts loaded in base.html
var bulkManager;

// Initialize bulk operations when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeBulkOperations();
    enableBulkActionsButton();
    setupFilterHandlers();
});

function initializeBulkOperations() {
    // Configuration for approval bulk operations
    const bulkConfig = {
        tableSelector: '#approvals-table',
        apiEndpoint: '/approvals/api/bulk-operations/',
        bulkButtonId: 'bulkActionsBtn',
        modalId: 'bulkOperationsModal',
        selectAllId: 'selectAllApprovals',
        checkboxClass: 'approval-checkbox',
        bulkCellClass: 'bulk-select-cell',
        bulkHeaderId: 'bulk-select-header',
        
        // Approval-specific operations with permissions
        operations: {
            bulk_approve: {
                label: 'Bulk Approve Requests',
                icon: 'bi bi-check-circle',
                permission: 'can_manage_system',
                description: 'Approve multiple pending requests at once',
                fields: [
                    {
                        name: 'approval_notes',
                        type: 'textarea',
                        label: 'Approval Notes',
                        required: false,
                        rows: 3,
                        placeholder: 'Optional notes for approval...'
                    },
                    {
                        name: 'execute_immediately',
                        type: 'checkbox',
                        label: 'Execute Actions Immediately',
                        value: true,
                        helpText: 'Execute the approved actions right away'
                    }
                ]
            },
            
            bulk_reject: {
                label: 'Bulk Reject Requests',
                icon: 'bi bi-x-circle',
                permission: 'can_manage_system',
                description: 'Reject multiple pending requests',
                fields: [
                    {
                        name: 'rejection_reason',
                        type: 'textarea',
                        label: 'Rejection Reason',
                        required: true,
                        rows: 3,
                        placeholder: 'Required: Reason for rejecting these requests...'
                    },
                    {
                        name: 'notify_requesters',
                        type: 'checkbox',
                        label: 'Notify Requesters',
                        value: true,
                        helpText: 'Send notification to users who created these requests'
                    }
                ]
            },
            
            update_priority: {
                label: 'Update Priority',
                icon: 'bi bi-flag',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'new_priority',
                        type: 'select',
                        label: 'New Priority Level',
                        required: true,
                        options: [
                            { value: 'low', label: 'Low' },
                            { value: 'medium', label: 'Medium' },
                            { value: 'high', label: 'High' },
                            { value: 'urgent', label: 'Urgent' }
                        ]
                    },
                    {
                        name: 'priority_reason',
                        type: 'textarea',
                        label: 'Reason for Priority Change',
                        required: false,
                        rows: 2,
                        placeholder: 'Optional reason for priority adjustment...'
                    }
                ]
            },
            
            reassign_approver: {
                label: 'Reassign to Different Approver',
                icon: 'bi bi-person-gear',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'new_approver_id',
                        type: 'select',
                        label: 'Assign to Approver',
                        required: true
                    },
                    {
                        name: 'reassignment_reason',
                        type: 'textarea',
                        label: 'Reassignment Reason',
                        required: false,
                        rows: 2,
                        placeholder: 'Reason for reassigning these requests...'
                    },
                    {
                        name: 'notify_new_approver',
                        type: 'checkbox',
                        label: 'Notify New Approver',
                        value: true,
                        helpText: 'Send notification to the new approver'
                    }
                ],
                loadData: function() {
                    loadApproversForBulk();
                }
            },
            
            extend_expiry: {
                label: 'Extend Request Expiry',
                icon: 'bi bi-calendar-plus',
                permission: 'can_manage_system',
                fields: [
                    {
                        name: 'extension_days',
                        type: 'number',
                        label: 'Extend by (days)',
                        required: true,
                        min: 1,
                        max: 30,
                        value: 7,
                        helpText: 'Number of days to extend expiry (1-30)'
                    },
                    {
                        name: 'extension_reason',
                        type: 'textarea',
                        label: 'Extension Reason',
                        required: false,
                        rows: 2,
                        placeholder: 'Reason for extending these requests...'
                    }
                ]
            },
            
            add_comments: {
                label: 'Add Comments to Requests',
                icon: 'bi bi-chat-text',
                permission: 'can_modify_assignments',
                fields: [
                    {
                        name: 'comment_category',
                        type: 'select',
                        label: 'Comment Category',
                        required: true,
                        options: [
                            { value: 'status_update', label: 'Status Update' },
                            { value: 'additional_info', label: 'Additional Information Required' },
                            { value: 'clarification', label: 'Clarification' },
                            { value: 'review_note', label: 'Review Note' },
                            { value: 'administrative', label: 'Administrative Note' }
                        ]
                    },
                    {
                        name: 'comment_text',
                        type: 'textarea',
                        label: 'Comment',
                        required: true,
                        rows: 4,
                        placeholder: 'Enter comment to add to selected requests...'
                    },
                    {
                        name: 'notify_requesters',
                        type: 'checkbox',
                        label: 'Notify Requesters',
                        value: false,
                        helpText: 'Send notification to users who created these requests'
                    }
                ]
            },
            
            export_selected: {
                label: 'Export Selected Requests',
                icon: 'bi bi-download',
                permission: 'can_view_devices',
                description: 'Export selected approval requests to various formats',
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
                        name: 'include_comments',
                        type: 'checkbox',
                        label: 'Include Comments',
                        value: true,
                        helpText: 'Include approval comments in export'
                    },
                    {
                        name: 'include_device_details',
                        type: 'checkbox',
                        label: 'Include Device Details',
                        value: true,
                        helpText: 'Include related device information'
                    }
                ]
            }
        },
        
        // Permission checks
        permissions: {
            can_modify_assignments: window.userPermissions?.can_modify_assignments || false,
            can_view_devices: window.userPermissions?.can_view_devices || false,
            can_manage_system: window.userPermissions?.can_manage_system || false
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
            refreshApprovalsList();
        }
    };
    
    // Initialize the bulk operations manager
    bulkManager = new BulkOperationsManager(bulkConfig);
    
    // Make it globally available
    window.bulkManager = bulkManager;
}

// Enhanced data loading functions
function loadApproversForBulk() {
    fetch('/core/api/users/?role=approvers')
        .then(response => response.json())
        .then(data => {
            const approverSelect = document.querySelector('select[name="new_approver_id"]');
            if (approverSelect) {
                approverSelect.innerHTML = '<option value="">Choose approver...</option>';
                data.results.forEach(user => {
                    approverSelect.innerHTML += `<option value="${user.id}">${user.full_name} - ${user.role || 'System Manager'}</option>`;
                });
            }
        })
        .catch(() => {
            const approverSelect = document.querySelector('select[name="new_approver_id"]');
            if (approverSelect) {
                approverSelect.innerHTML = '<option value="">Error loading approvers</option>';
            }
        });
}

function setupFilterHandlers() {
    // Handle search and filter inputs
    const statusSelect = document.querySelector('select[name="status"]');
    const prioritySelect = document.querySelector('select[name="priority"]');
    const requestTypeSelect = document.querySelector('select[name="request_type"]');
    
    // Add event listeners for manual filter handling
    [statusSelect, prioritySelect, requestTypeSelect].forEach(element => {
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

// Approval-specific functions
function exportApprovals() {
    // Get current filter values
    const statusValue = document.querySelector('select[name="status"]')?.value || '';
    const priorityValue = document.querySelector('select[name="priority"]')?.value || '';
    const requestTypeValue = document.querySelector('select[name="request_type"]')?.value || '';
    
    const params = new URLSearchParams();
    if (statusValue) params.append('status', statusValue);
    if (priorityValue) params.append('priority', priorityValue);
    if (requestTypeValue) params.append('request_type', requestTypeValue);
    params.append('export', 'csv');
    
    window.open(`/approvals/api/approvals/?${params.toString()}`, '_blank');
}

function refreshApprovalsList() {
    // Trigger HTMX refresh for the approvals table
    htmx.ajax('GET', '/approvals/api/list/', {
        target: '#approvals-table',
        swap: 'innerHTML'
    });
}

// Quick action functions
function quickApprove(requestId) {
    if (!confirm('Are you sure you want to approve this request?')) {
        return;
    }
    
    fetch(`/approvals/api/${requestId}/approve/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            notes: 'Quick approved'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('danger', data.error);
        } else {
            showAlert('success', data.message);
            refreshApprovalsList();
        }
    })
    .catch(error => {
        showAlert('danger', 'Error approving request');
    });
}

function quickReject(requestId) {
    const reason = prompt('Please enter a reason for rejection:');
    if (!reason || reason.trim() === '') {
        return;
    }
    
    fetch(`/approvals/api/${requestId}/reject/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            reason: reason.trim()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('danger', data.error);
        } else {
            showAlert('success', data.message);
            refreshApprovalsList();
        }
    })
    .catch(error => {
        showAlert('danger', 'Error rejecting request');
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
window.exportApprovals = exportApprovals;
window.refreshApprovalsList = refreshApprovalsList;
window.showAlert = showAlert;
window.toggleBulkMode = toggleBulkMode;
window.quickApprove = quickApprove;
window.quickReject = quickReject;

// HTMX integration
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.elt.id === 'approvals-table') {
        console.log('Approvals table refreshed');
        // Re-initialize bulk operations after HTMX updates
        if (bulkManager) {
            bulkManager.init();
        }
    }
});