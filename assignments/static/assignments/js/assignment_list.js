function showReturnModal(deviceId) {
    // Load return device modal content via HTMX
    htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
        target: '#return-modal-content',
        swap: 'innerHTML'
    });
    
    const modal = new bootstrap.Modal(document.getElementById('returnModal'));
    modal.show();
}

// Global function to refresh assignments
function refreshAssignments() {
    // Trigger refresh of assignment list
    const event = new CustomEvent('refreshAssignments');
    document.dispatchEvent(event);
}

// Make it available globally
window.refreshAssignments = refreshAssignments;