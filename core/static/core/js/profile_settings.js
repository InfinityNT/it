document.addEventListener('DOMContentLoaded', function() {
    // Handle toggle switches with immediate feedback
    document.body.addEventListener('change', function(e) {
        if (e.target.classList.contains('action-toggle')) {
            const actionCode = e.target.dataset.actionCode;
            const isEnabled = e.target.checked;
            const label = e.target.nextElementSibling;
            
            // Update the label text immediately
            label.textContent = isEnabled ? 'Enabled' : 'Disabled';
            
            // Send AJAX request
            fetch('/api/quick-actions-toggle/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `action_code=${actionCode}&is_enabled=${isEnabled}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the quick actions sidebar without full refresh
                    const quickActionsSection = document.getElementById('quick-actions-section');
                    if (quickActionsSection) {
                        htmx.trigger(quickActionsSection, 'load');
                    }
                    showAlert('success', data.message);
                } else {
                    showAlert('danger', 'Failed to update action');
                    // Revert the toggle
                    e.target.checked = !isEnabled;
                    label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
                }
            })
            .catch(error => {
                showAlert('danger', 'An error occurred');
                // Revert the toggle
                e.target.checked = !isEnabled;
                label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
            });
        }
    });
});

function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;
    
    // Fallback to cookie
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
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