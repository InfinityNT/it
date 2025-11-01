function showUserReturnModal(deviceId) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('userReturnModal');
    if (!modal) {
        // Create the modal HTML
        const modalHTML = `
            <div class="modal fade" id="userReturnModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content" id="user-return-modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Loading...</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="d-flex justify-content-center p-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('userReturnModal');
    }
    
    // Load return device modal content via HTMX
    htmx.ajax('GET', `/assignments/api/return-device-modal/${deviceId}/`, {
        target: '#user-return-modal-content',
        swap: 'innerHTML'
    });
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}