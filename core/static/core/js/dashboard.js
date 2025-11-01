let searchTimeout;
const searchInput = document.getElementById('globalSearch');
const searchResults = document.getElementById('searchResults');
const clearButton = document.getElementById('clearSearch');
const searchTip = document.getElementById('searchTip');

// Show/hide search tip based on focus and content
function updateSearchTip() {
    const query = searchInput.value.trim();
    if (document.activeElement === searchInput && query.length === 0) {
        searchTip.style.display = 'block';
    } else {
        searchTip.style.display = 'none';
    }
}

// Focus and blur events for search tip
searchInput.addEventListener('focus', updateSearchTip);
searchInput.addEventListener('blur', updateSearchTip);

// Search functionality
searchInput.addEventListener('input', function() {
    const query = this.value.trim();
    
    // Update search tip visibility
    updateSearchTip();
    
    // Show/hide clear button
    if (query.length > 0) {
        clearButton.style.display = 'block';
    } else {
        clearButton.style.display = 'none';
        hideSearchResults();
        return;
    }
    
    // Debounce search requests
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if (query.length >= 2) {
            performSearch(query);
        } else {
            hideSearchResults();
        }
    }, 300);
});

// Clear search
clearButton.addEventListener('click', function() {
    searchInput.value = '';
    clearButton.style.display = 'none';
    hideSearchResults();
    searchInput.focus();
    updateSearchTip(); // Update tip visibility after clearing
});

// Hide results when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.position-relative')) {
        hideSearchResults();
    }
});

// Keyboard navigation
searchInput.addEventListener('keydown', function(event) {
    const items = searchResults.querySelectorAll('.search-result-item');
    const selected = searchResults.querySelector('.search-result-item.active');
    
    if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (selected) {
            selected.classList.remove('active');
            const next = selected.nextElementSibling;
            if (next) {
                next.classList.add('active');
            } else {
                items[0]?.classList.add('active');
            }
        } else {
            items[0]?.classList.add('active');
        }
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (selected) {
            selected.classList.remove('active');
            const prev = selected.previousElementSibling;
            if (prev) {
                prev.classList.add('active');
            } else {
                items[items.length - 1]?.classList.add('active');
            }
        } else {
            items[items.length - 1]?.classList.add('active');
        }
    } else if (event.key === 'Enter') {
        event.preventDefault();
        if (selected) {
            selected.click();
        }
    } else if (event.key === 'Escape') {
        hideSearchResults();
    }
});

function performSearch(query) {
    showSearchLoading();
    
    fetch(`/api/dashboard/search/?q=${encodeURIComponent(query)}`, {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        displaySearchResults(data.results || []);
    })
    .catch(error => {
        console.error('Search error:', error);
        showSearchError();
    });
}

function showSearchLoading() {
    searchResults.innerHTML = `
        <div class="search-result-item text-center">
            <div class="d-flex align-items-center justify-content-center">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                <span>Searching...</span>
            </div>
        </div>
    `;
    searchResults.style.display = 'block';
}

function showSearchError() {
    searchResults.innerHTML = `
        <div class="search-result-item text-center text-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Search error. Please try again.
        </div>
    `;
    searchResults.style.display = 'block';
}

function displaySearchResults(results) {
    if (results.length === 0) {
        searchResults.innerHTML = `
            <div class="search-result-item text-center text-muted">
                <i class="bi bi-search me-2"></i>
                No devices found matching your search.
            </div>
        `;
    } else {
        searchResults.innerHTML = results.map(device => `
            <div class="search-result-item" onclick="navigateToDevice(${device.id})">
                <div class="search-result-device">
                    <div class="search-result-info">
                        <div class="search-result-asset-tag">${device.asset_tag}</div>
                        <div class="search-result-details">
                            ${device.manufacturer} ${device.model_name}
                            ${device.serial_number ? `• S/N: ${device.serial_number}` : ''}
                            ${device.assigned_to ? `• Assigned to: ${device.assigned_to}` : ''}
                            ${device.location ? `• Location: ${device.location}` : ''}
                        </div>
                    </div>
                    <div class="search-result-status">
                        <span class="badge ${getStatusBadgeClass(device.status)}">${device.status_display}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    searchResults.style.display = 'block';
}

function hideSearchResults() {
    searchResults.style.display = 'none';
    // Remove active states
    searchResults.querySelectorAll('.search-result-item.active').forEach(item => {
        item.classList.remove('active');
    });
}

function navigateToDevice(deviceId) {
    window.location.href = `/devices/${deviceId}/`;
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'available': return 'bg-success';
        case 'assigned': return 'bg-warning';
        case 'retired': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

// Auto-focus search on Ctrl+K or Cmd+K
document.addEventListener('keydown', function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        searchInput.focus();
        updateSearchTip(); // Show tip when focusing with keyboard shortcut
    }
});