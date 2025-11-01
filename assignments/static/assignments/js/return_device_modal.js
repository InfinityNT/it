// Handle return form submission
document.getElementById('returnDeviceForm').addEventListener('htmx:afterRequest', function(event) {
    const spinner = document.getElementById('return-spinner');
    spinner.classList.add('d-none');
    
    if (event.detail.xhr.status === 200) {
        // Success - close modal and refresh lists
        const deviceModal = document.getElementById('deviceModal');
        const returnModal = document.getElementById('returnModal');
        const userReturnModal = document.getElementById('userReturnModal');
        const deviceReturnModal = document.getElementById('deviceReturnModal');
        
        // Close whichever modal is open
        if (deviceModal && bootstrap.Modal.getInstance(deviceModal)) {
            bootstrap.Modal.getInstance(deviceModal).hide();
        }
        if (returnModal && bootstrap.Modal.getInstance(returnModal)) {
            bootstrap.Modal.getInstance(returnModal).hide();
        }
        if (userReturnModal && bootstrap.Modal.getInstance(userReturnModal)) {
            bootstrap.Modal.getInstance(userReturnModal).hide();
        }
        if (deviceReturnModal && bootstrap.Modal.getInstance(deviceReturnModal)) {
            bootstrap.Modal.getInstance(deviceReturnModal).hide();
        }
        
        // Show success message
        const response = JSON.parse(event.detail.xhr.responseText);
        showAlert('success', response.message);
        
        // Refresh the appropriate list
        if (window.refreshDeviceList) {
            window.refreshDeviceList();
        }
        if (window.refreshAssignments) {
            window.refreshAssignments();
        }
        
        // Refresh user assignments if we're on a user detail page
        const currentAssignments = document.getElementById('currentAssignments');
        if (currentAssignments) {
            htmx.trigger(currentAssignments, 'refresh');
        }
        
        const assignmentHistory = document.getElementById('assignmentHistory');
        if (assignmentHistory) {
            htmx.trigger(assignmentHistory, 'refresh');
        }
        
        // Refresh device assignment history if we're on device detail page
        const deviceAssignmentHistory = document.getElementById('assignment-history');
        if (deviceAssignmentHistory) {
            htmx.trigger(deviceAssignmentHistory, 'refresh');
        }
        
        // If we're on device detail page, reload to show updated status
        if (window.location.pathname.includes('/devices/') && window.location.pathname.includes('/')) {
            setTimeout(() => window.location.reload(), 1000);
            return;
        }
        
        // Fallback - reload page if no refresh functions available
        if (!window.refreshDeviceList && !window.refreshAssignments && !currentAssignments) {
            window.location.reload();
        }
    } else {
        // Error handling
        try {
            const response = JSON.parse(event.detail.xhr.responseText);
            showAlert('danger', 'Error: ' + (response.error || 'Failed to return device'));
        } catch (e) {
            showAlert('danger', 'An error occurred while returning the device');
        }
    }
});

// Handle form submission start
document.getElementById('returnDeviceForm').addEventListener('htmx:beforeRequest', function(event) {
    const spinner = document.getElementById('return-spinner');
    spinner.classList.remove('d-none');
});

// Helper function to show alerts
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}