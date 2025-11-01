let currentUserId = {{ user_profile.id }};

document.addEventListener('DOMContentLoaded', function() {
    loadUserStatistics();
    loadUserActivity();
});

function loadUserStatistics() {
    // Load audit log statistics for this user
    fetch(`/api/audit-logs/?user=${currentUserId}`)
        .then(response => response.json())
        .then(data => {
            const logs = data.results || data;
            
            // Calculate statistics
            const totalActions = logs.length;
            const oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
            
            const recentActions = logs.filter(log => 
                new Date(log.timestamp) >= oneWeekAgo
            ).length;
            
            const loginActions = logs.filter(log => 
                log.action === 'login'
            ).length;
            
            // Update statistics display
            document.getElementById('totalActions').textContent = totalActions;
            document.getElementById('recentActions').textContent = recentActions;
            document.getElementById('loginCount').textContent = loginActions;
            
            // Format last login
            const lastLoginElement = document.getElementById('lastLogin');
            const lastLoginStr = '{{ user_profile.last_login|date:"c" }}'; // ISO format
            
            if (lastLoginStr && lastLoginStr !== '' && lastLoginStr !== 'None') {
                try {
                    const lastLogin = new Date(lastLoginStr);
                    const now = new Date();
                    const diffDays = Math.floor((now - lastLogin) / (1000 * 60 * 60 * 24));
                    
                    if (diffDays === 0) {
                        lastLoginElement.textContent = 'Today';
                    } else if (diffDays === 1) {
                        lastLoginElement.textContent = '1 day ago';
                    } else if (diffDays < 7) {
                        lastLoginElement.textContent = `${diffDays} days ago`;
                    } else {
                        lastLoginElement.textContent = lastLogin.toLocaleDateString();
                    }
                } catch (e) {
                    lastLoginElement.textContent = 'Unknown';
                }
            } else {
                lastLoginElement.textContent = 'Never';
            }
        })
        .catch(error => {
            console.error('Error loading user statistics:', error);
            // Set default values on error
            document.getElementById('totalActions').textContent = '0';
            document.getElementById('recentActions').textContent = '0';
            document.getElementById('loginCount').textContent = '0';
            document.getElementById('lastLogin').textContent = 'Unknown';
        });
}

function loadUserActivity() {
    // Load both types of activity
    loadProfileChanges();
    loadUserActions();
}

function loadProfileChanges() {
    // Load audit logs for actions performed ON this user (profile changes)
    fetch(`/api/audit-logs/?model_name=User&object_id=${currentUserId}&limit=10`)
        .then(response => response.json())
        .then(data => {
            const logs = data.results || data;
            const container = document.getElementById('profileChangesActivity');
            
            if (logs.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">No profile changes recorded</p>';
                return;
            }
            
            container.innerHTML = renderActivityList(logs);
        })
        .catch(error => {
            console.error('Error loading profile changes:', error);
            document.getElementById('profileChangesActivity').innerHTML = 
                '<p class="text-muted text-center">Error loading profile changes</p>';
        });
}

function loadUserActions() {
    // Load audit logs for actions performed BY this user
    fetch(`/api/audit-logs/?user=${currentUserId}&limit=10`)
        .then(response => response.json())
        .then(data => {
            const logs = data.results || data;
            const container = document.getElementById('userActionsActivity');
            
            if (logs.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">No user actions recorded</p>';
                return;
            }
            
            container.innerHTML = renderActivityList(logs);
        })
        .catch(error => {
            console.error('Error loading user actions:', error);
            document.getElementById('userActionsActivity').innerHTML = 
                '<p class="text-muted text-center">Error loading user actions</p>';
        });
}

function renderActivityList(logs) {
    let activityHtml = '<div class="list-group list-group-flush">';
    logs.forEach(log => {
        const date = new Date(log.timestamp);
        // Get icon and color for action
        const actionIcon = getActionIcon(log.action);
        const actionColor = getActionColor(log.action);
        
        // Fallback to ensure we always have an icon
        const finalIcon = actionIcon || 'bi-circle-fill';
        const finalColor = actionColor || 'primary';
        
        const actionText = getActionText(log.action, log.model_name, log.changes, log.object_repr);
        
        activityHtml += `
            <div class="list-group-item border-0 px-0">
                <div class="d-flex align-items-center">
                    <div class="flex-shrink-0 me-3">
                        <i class="bi ${finalIcon} text-${finalColor}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-bold">${actionText}</div>
                        <small class="text-muted">${log.object_repr || (log.model_name === 'User' ? 'User account' : log.model_name)}</small>
                        <div class="small text-muted">${date.toLocaleDateString()} ${date.toLocaleTimeString()}</div>
                    </div>
                </div>
            </div>
        `;
    });
    activityHtml += '</div>';
    return activityHtml;
}

function getActionIcon(action) {
    const icons = {
        'create': 'bi-plus-circle-fill',
        'update': 'bi-pencil-fill',
        'delete': 'bi-trash-fill',
        'assign': 'bi-arrow-right-circle-fill',
        'unassign': 'bi-arrow-left-circle-fill',
        'login': 'bi-box-arrow-in-right',
        'logout': 'bi-box-arrow-right',
        'updated': 'bi-pencil-fill',
        'created': 'bi-plus-circle-fill',
        'deleted': 'bi-trash-fill'
    };
    return icons[action] || 'bi-circle-fill';
}

function getActionColor(action) {
    const colors = {
        'create': 'success',
        'update': 'primary',
        'delete': 'danger',
        'assign': 'info',
        'unassign': 'warning',
        'login': 'success',
        'logout': 'secondary',
        'created': 'success',
        'updated': 'primary',
        'deleted': 'danger'
    };
    return colors[action] || 'secondary';
}

function getActionText(action, modelName, changes, objectRepr) {
    // For user actions, provide more specific descriptions
    if (modelName === 'User') {
        if (action === 'create') {
            return 'Created user account';
        } else if (action === 'update') {
            // Check if it's a password change
            if (typeof changes === 'object' && changes.password_changed) {
                return 'Changed password';
            }
            // Check for activation/deactivation in string format
            if (typeof changes === 'string') {
                if (changes.includes('activated')) {
                    return 'Activated user account';
                } else if (changes.includes('deactivated')) {
                    return 'Deactivated user account';
                }
            }
            // Check for activation/deactivation in object format
            if (typeof changes === 'object' && changes.status_changed) {
                if (changes.status_changed === 'activated') {
                    return 'Activated user account';
                } else if (changes.status_changed === 'deactivated') {
                    return 'Deactivated user account';
                }
            }
            return 'Updated user profile';
        }
    }
    
    const actionTexts = {
        'create': `Created ${modelName}`,
        'update': `Updated ${modelName}`,
        'delete': `Deleted ${modelName}`,
        'assign': `Assigned ${modelName}`,
        'unassign': `Unassigned ${modelName}`,
        'login': 'Logged in',
        'logout': 'Logged out'
    };
    
    return actionTexts[action] || `${action.charAt(0).toUpperCase() + action.slice(1)} ${modelName}`;
}


function toggleUserStatus(userId, activate) {
    const action = activate ? 'activate' : 'deactivate';
    const message = activate ? 'activate' : 'deactivate';
    
    if (confirm(`Are you sure you want to ${message} this user?`)) {
        fetch(`/api/users/${userId}/toggle-status/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                location.reload(); // Refresh to show updated status
            } else {
                alert(data.error || 'Status update failed');
            }
        })
        .catch(error => {
            alert('An error occurred during status update');
            console.error('Error:', error);
        });
    }
}

function resetPassword(userId) {
    if (confirm('Are you sure you want to reset this user\'s password?')) {
        alert('Password reset functionality coming soon!');
    }
}

// Refresh activity when needed
function refreshUserData() {
    loadUserStatistics();
    loadUserActivity();
}