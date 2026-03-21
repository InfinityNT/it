/**
 * Devices App - Core functionality
 * Wrapped in initialization function for SPA compatibility
 */

// Global variable for current device context
var currentDeviceId = null;

// Critical functions defined globally so they're always available
function showAssignModal(deviceId) {
    currentDeviceId = deviceId;

    // Load assign device modal with preselected device via HTMX
    htmx.ajax('GET', `/assignments/assign/${deviceId}/`, {
        target: '#dynamicModalContent',
        swap: 'innerHTML'
    }).then(() => {
        // Show the modal after content is loaded
        const modalEl = document.getElementById('dynamicModal');
        if (modalEl) {
            // Get or create modal instance
            let modal = bootstrap.Modal.getInstance(modalEl);
            if (!modal) {
                modal = new bootstrap.Modal(modalEl);
            }
            modal.show();
        } else {
            console.error('dynamicModal element not found');
        }
    });
}

function showUnassignModal(deviceId) {
    currentDeviceId = deviceId;

    // Verify modal exists before proceeding
    const modalEl = document.getElementById('dynamicModal');
    if (!modalEl) {
        console.error('dynamicModal element not found in DOM');
        console.log('Available modals:', document.querySelectorAll('.modal'));
        showAlert('Modal container not found. Please refresh the page.', 'danger');
        return;
    }

    // Load return device modal content via HTMX using standardized dynamicModal
    htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
        target: '#dynamicModalContent',
        swap: 'innerHTML'
    }).then(() => {
        // Get modal instance after content is loaded
        let modal = bootstrap.Modal.getInstance(modalEl);
        if (!modal) {
            modal = new bootstrap.Modal(modalEl);
        }
        modal.show();
    }).catch(error => {
        console.error('Error loading return device modal:', error);
        showAlert('Failed to load return device form. Please try again.', 'danger');
    });
}

function showEditModal(deviceId) {
    currentDeviceId = deviceId;

    // Verify modal exists before proceeding
    const modalEl = document.getElementById('dynamicModal');
    if (!modalEl) {
        console.error('dynamicModal element not found in DOM');
        showAlert('Modal container not found. Please refresh the page.', 'danger');
        return;
    }

    // Load edit device modal content via HTMX
    htmx.ajax('GET', `/devices/${deviceId}/edit/`, {
        target: '#dynamicModalContent',
        swap: 'innerHTML'
    }).then(() => {
        // Get modal instance after content is loaded
        let modal = bootstrap.Modal.getInstance(modalEl);
        if (!modal) {
            modal = new bootstrap.Modal(modalEl);
        }
        modal.show();
    }).catch(error => {
        console.error('Error loading edit device modal:', error);
        showAlert('Failed to load edit device form. Please try again.', 'danger');
    });
}

function exportDevices() {
    window.open('/devices/search/?export=csv', '_blank');
}

function refreshDeviceList() {
    htmx.ajax('GET', '/devices/api/devices/', {
        target: '#devices-table',
        swap: 'innerHTML'
    });
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

// Export functions immediately so they're always available
window.showAssignModal = showAssignModal;
window.showUnassignModal = showUnassignModal;
window.showEditModal = showEditModal;
window.exportDevices = exportDevices;
window.refreshDeviceList = refreshDeviceList;
window.showAlert = showAlert;

function initializeDevicesPage() {
    // Guard: Only run if we're on devices page
    if (!document.querySelector('#devices-table')) {
        console.warn('Devices table not found, skipping initialization');
        return;
    }

    // Prevent double initialization
    if (window.devicesInitialized) {
        console.log('Devices already initialized, skipping');
        return;
    }
    window.devicesInitialized = true;
    console.log('Starting devices initialization...');

    // HTMX integration
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.elt.id === 'devices-table') {
            console.log('Devices table refreshed');
        }
    });

    console.log('Devices page initialization complete');
}

// Export initialization function
window.initializeDevicesPage = initializeDevicesPage;

// Auto-initialize on direct page load (non-HTMX)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDevicesPage);
} else {
    initializeDevicesPage();
}
