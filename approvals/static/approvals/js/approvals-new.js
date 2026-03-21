/**
 * Approvals App - Core functionality
 */

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupFilterHandlers();
});

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
window.quickApprove = quickApprove;
window.quickReject = quickReject;

// HTMX integration
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.elt.id === 'approvals-table') {
        console.log('Approvals table refreshed');
    }
});
