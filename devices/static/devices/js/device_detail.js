let currentDeviceId = {{ device.id }};

function showAssignModal(deviceId) {
    // Load users for assignment
    fetch('/api/users/json/')
        .then(response => response.json())
        .then(data => {
            const userSelect = document.getElementById('assignUser');
            userSelect.innerHTML = '<option value="">Choose a user...</option>';
            data.results.forEach(user => {
                userSelect.innerHTML += `<option value="${user.id}">${user.first_name} ${user.last_name} (${user.username})</option>`;
            });
        });
    
    const modal = new bootstrap.Modal(document.getElementById('assignModal'));
    modal.show();
}

function showUnassignModal(deviceId) {
    // Load return device modal content via HTMX
    htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
        target: '#device-return-modal-content',
        swap: 'innerHTML'
    });
    
    const modal = new bootstrap.Modal(document.getElementById('deviceReturnModal'));
    modal.show();
}

function submitAssignment() {
    const form = document.getElementById('assignForm');
    const formData = new FormData(form);
    
    fetch(`/devices/api/devices/${currentDeviceId}/assign/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: parseInt(formData.get('user_id')),
            expected_return_date: formData.get('expected_return_date'),
            notes: formData.get('notes')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            bootstrap.Modal.getInstance(document.getElementById('assignModal')).hide();
            showAlert('success', data.message);
            // Refresh the page to show updated assignment
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('danger', data.error || 'Assignment failed');
        }
    })
    .catch(error => {
        showAlert('danger', 'An error occurred during assignment');
    });
}

// Add alert functionality
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}