// Use event delegation to handle toggle switches (works with HTMX-loaded content)
document.addEventListener('change', function(event) {
    const toggle = event.target;
    if (!toggle.classList.contains('action-toggle')) return;

    const actionCode = toggle.dataset.actionCode;
    const isEnabled = toggle.checked;
    const label = toggle.nextElementSibling;

    // Update the label text
    label.textContent = isEnabled ? 'Enabled' : 'Disabled';

    // Send AJAX request to the toggle API endpoint
    fetch('/api/quick-actions/toggle/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `action_code=${actionCode}&is_enabled=${isEnabled}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add visual feedback on the toggle item
            const actionItem = toggle.closest('.action-item');
            if (actionItem) {
                actionItem.classList.add('save-success');

                // Add checkmark icon
                const feedbackIcon = document.createElement('span');
                feedbackIcon.className = 'save-feedback-icon ms-2';
                feedbackIcon.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                label.parentNode.appendChild(feedbackIcon);

                // Remove feedback after animation
                setTimeout(() => {
                    actionItem.classList.remove('save-success');
                    feedbackIcon.remove();
                }, 2000);
            }
            // Show message to refresh
            showAlert('success', 'Quick action updated. Refresh the page to see changes in the sidebar.');
        } else {
            showAlert('danger', 'Failed to update action');
            // Revert the toggle
            toggle.checked = !isEnabled;
            label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
        }
    })
    .catch(error => {
        showAlert('danger', 'An error occurred');
        // Revert the toggle
        toggle.checked = !isEnabled;
        label.textContent = !isEnabled ? 'Enabled' : 'Disabled';
    });
});

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
    }

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
