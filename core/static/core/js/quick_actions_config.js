document.addEventListener('DOMContentLoaded', function() {
    // Handle toggle switches
    const toggles = document.querySelectorAll('.action-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const actionCode = this.dataset.actionCode;
            const isEnabled = this.checked;
            const label = this.nextElementSibling;
            
            // Update the label text
            label.textContent = isEnabled ? 'Enabled' : 'Disabled';
            
            // Send AJAX request
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `action=toggle_action&action_code=${actionCode}&is_enabled=${isEnabled}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                } else {
                    showAlert('danger', 'Failed to update action');
                    // Revert the toggle
                    this.checked = !isEnabled;
                    label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
                }
            })
            .catch(error => {
                showAlert('danger', 'An error occurred');
                // Revert the toggle
                this.checked = !isEnabled;
                label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
            });
        });
    });
});

function saveConfiguration() {
    showAlert('success', 'Configuration saved successfully!');
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