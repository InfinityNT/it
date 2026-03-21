/**
 * User Management - Core functionality
 */

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
