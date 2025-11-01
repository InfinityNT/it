let currentPage = 1;
let currentView = 'list';
let searchTimeout;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadInitialResults();
    
    // Form submission
    document.getElementById('advancedSearchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        performSearch();
    });
    
    // Real-time search on text input
    document.getElementById('searchQuery').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 500);
    });
    
    // Filter change listeners
    document.querySelectorAll('input[type="checkbox"], select, input[type="radio"]').forEach(element => {
        element.addEventListener('change', performSearch);
    });
    
    // Date inputs
    document.querySelectorAll('input[type="date"]').forEach(element => {
        element.addEventListener('change', performSearch);
    });
});

function loadInitialResults() {
    // Load all devices initially
    performSearch();
}

function performSearch(page = 1) {
    currentPage = page;
    showLoading();
    
    const formData = new FormData(document.getElementById('advancedSearchForm'));
    const params = new URLSearchParams();
    
    // Add form data to params - handle checkboxes properly
    for (let [key, value] of formData.entries()) {
        if (value && value.trim && value.trim()) {
            params.append(key, value);
        } else if (typeof value === 'string' && value) {
            params.append(key, value);
        }
    }
    
    // Add page parameter
    params.append('page', page);
    
    // Debug: log the params being sent
    console.log('Search params:', params.toString());
    
    fetch(`/devices/api/advanced-search/?${params.toString()}`, {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Accept': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        console.log('Search response:', data);
        displayResults(data.results || []);
        updateResultCount(data.total || 0);
        updatePagination(data.pagination || {});
        updateActiveFilters();
    })
    .catch(error => {
        hideLoading();
        console.error('Search error:', error);
        showError(`Search failed: ${error.message}`);
    });
}

function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('searchResults').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('searchResults').style.display = 'block';
}

function displayResults(devices) {
    const container = document.getElementById('searchResults');
    
    if (devices.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-search display-1 mb-3"></i>
                <h5>No devices found</h5>
                <p>Try adjusting your search filters.</p>
            </div>
        `;
        return;
    }
    
    if (currentView === 'grid') {
        displayGridView(devices);
    } else {
        displayListView(devices);
    }
}

function displayGridView(devices) {
    const container = document.getElementById('searchResults');
    container.className = 'grid-view';
    
    const html = `
        <div class="row">
            ${devices.map(device => `
                <div class="col-md-4 col-lg-3 mb-3">
                    <div class="card device-card h-100" onclick="navigateToDevice(${device.id})">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">${device.asset_tag}</h6>
                                <span class="badge ${getStatusBadgeClass(device.status)}">${device.status_display}</span>
                            </div>
                            <p class="card-text">
                                <small class="text-muted">${device.manufacturer} ${device.model_name}</small><br>
                                <small class="text-muted">S/N: ${device.serial_number || 'N/A'}</small>
                            </p>
                            ${device.assigned_to ? `
                                <p class="card-text">
                                    <small><i class="bi bi-person"></i> ${device.assigned_to}</small>
                                </p>
                            ` : ''}
                            ${device.location ? `
                                <p class="card-text">
                                    <small><i class="bi bi-geo-alt"></i> ${device.location}</small>
                                </p>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = html;
}

function displayListView(devices) {
    const container = document.getElementById('searchResults');
    container.className = 'list-view';
    
    const html = devices.map(device => `
        <div class="device-item" onclick="navigateToDevice(${device.id})">
            <div class="row align-items-center">
                <div class="col-md-3">
                    <div class="d-flex align-items-center">
                        <div class="device-icon me-2">
                            <i class="bi ${getDeviceIcon(device.category)} text-primary"></i>
                        </div>
                        <div>
                            <strong>${device.asset_tag}</strong><br>
                            <small class="text-muted">${device.serial_number || 'No S/N'}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div>
                        ${device.manufacturer} ${device.model_name}<br>
                        <small class="text-muted">${device.category}</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <span class="badge ${getStatusBadgeClass(device.status)}">${device.status_display}</span>
                </div>
                <div class="col-md-2">
                    ${device.assigned_to ? `
                        <div>
                            <i class="bi bi-person"></i> ${device.assigned_to}<br>
                            <small class="text-muted">${device.assigned_date ? new Date(device.assigned_date).toLocaleDateString() : ''}</small>
                        </div>
                    ` : '<span class="text-muted">Unassigned</span>'}
                </div>
                <div class="col-md-2">
                    ${device.location ? `<i class="bi bi-geo-alt"></i> ${device.location}` : '<span class="text-muted">No location</span>'}
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function toggleView(view) {
    currentView = view;
    
    // Update button states
    document.getElementById('gridViewBtn').classList.toggle('active', view === 'grid');
    document.getElementById('listViewBtn').classList.toggle('active', view === 'list');
    
    // Re-render current results
    const container = document.getElementById('searchResults');
    if (container.children.length > 0) {
        performSearch(currentPage);
    }
}

function updateResultCount(count) {
    document.getElementById('resultCount').textContent = count.toLocaleString();
}

function updatePagination(pagination) {
    // Implementation for pagination
    const nav = document.getElementById('paginationNav');
    if (pagination.total_pages > 1) {
        nav.style.display = 'block';
        // Generate pagination HTML
    } else {
        nav.style.display = 'none';
    }
}

function updateActiveFilters() {
    // Show active filters as removable tags
    // Implementation for active filter display
}

function quickFilter(type) {
    console.log('Quick filter clicked:', type);
    
    // Clear all filters first
    clearAllFilters();
    
    // Clear all quick filter button states
    document.querySelectorAll('[id^="quick-"]').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.remove('btn-success', 'btn-warning', 'btn-info', 'btn-danger', 'btn-secondary');
        
        // Reset to original outline style based on button ID
        if (btn.id === 'quick-available') {
            btn.className = 'btn btn-outline-success btn-sm';
        } else if (btn.id === 'quick-assigned') {
            btn.className = 'btn btn-outline-warning btn-sm';
        } else if (btn.id === 'quick-overdue') {
            btn.className = 'btn btn-outline-danger btn-sm';
        } else if (btn.id === 'quick-warranty') {
            btn.className = 'btn btn-outline-secondary btn-sm';
        }
    });
    
    // Set the appropriate filter and button state based on type
    let button;
    switch (type) {
        case 'available':
            document.getElementById('status_available').checked = true;
            button = document.getElementById('quick-available');
            button.classList.remove('btn-outline-success');
            button.classList.add('btn-success', 'active');
            break;
        case 'assigned':
            document.getElementById('status_assigned').checked = true;
            button = document.getElementById('quick-assigned');
            button.classList.remove('btn-outline-warning');
            button.classList.add('btn-warning', 'active');
            break;
        case 'overdue':
            // Filter for assigned devices that are overdue
            document.getElementById('status_assigned').checked = true;
            button = document.getElementById('quick-overdue');
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-danger', 'active');
            // TODO: Add special logic for overdue items in API
            break;
    }
    
    console.log('Filter set, triggering search...');
    // Trigger the search with the new filters
    performSearch(1);
}

function clearAllFilters() {
    document.getElementById('advancedSearchForm').reset();

    // Reset all quick filter buttons to outline style
    document.getElementById('quick-available').className = 'btn btn-outline-success btn-sm';
    document.getElementById('quick-assigned').className = 'btn btn-outline-warning btn-sm';
    document.getElementById('quick-overdue').className = 'btn btn-outline-danger btn-sm';

    // Don't automatically search when clearing - let the caller decide
}

function exportResults() {
    const formData = new FormData(document.getElementById('advancedSearchForm'));
    const params = new URLSearchParams();
    
    for (let [key, value] of formData.entries()) {
        if (value.trim()) {
            params.append(key, value);
        }
    }
    
    // Add export parameter
    params.append('export', 'csv');
    
    window.open(`/devices/api/advanced-search/?${params.toString()}`, '_blank');
}

function navigateToDevice(deviceId) {
    window.location.href = `/devices/${deviceId}/`;
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'available': return 'bg-success';
        case 'assigned': return 'bg-warning text-dark';
        case 'retired': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

function getDeviceIcon(category) {
    switch(category?.toLowerCase()) {
        case 'laptop': return 'bi-laptop';
        case 'desktop': return 'bi-pc-display';
        case 'phone': return 'bi-phone';
        case 'monitor': return 'bi-display';
        case 'tablet': return 'bi-tablet';
        case 'printer': return 'bi-printer';
        default: return 'bi-device-hdd';
    }
}

function showError(message) {
    document.getElementById('searchResults').innerHTML = `
        <div class="alert alert-danger text-center">
            <i class="bi bi-exclamation-triangle"></i>
            ${message}
        </div>
    `;
}

function getCsrfToken() {
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfTokenElement ? csrfTokenElement.value : '';
}