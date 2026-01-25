/**
 * Dynamic Custom Report Builder - Frontend Logic
 * Supports multi-source report generation
 */

let reportSchema = {};
let selectedDataSources = [];
let primarySource = null;
let selectedFields = [];
let isInitialized = false;

// Initialize when modal is shown
function initializeReportBuilder() {
    if (isInitialized) {
        console.log('[Report Builder] Already initialized');
        return;
    }

    const modal = document.getElementById('customReportModal');
    if (!modal) {
        console.warn('[Report Builder] Modal element not found');
        return;
    }

    console.log('[Report Builder] Initializing...');
    // Load schema and initialize
    loadReportSchema();
    initializeEventListeners();
    isInitialized = true;
    console.log('[Report Builder] Initialization complete');
}

// Setup modal event listener
function setupModalListener() {
    const modal = document.getElementById('customReportModal');
    if (modal && !modal.hasAttribute('data-report-builder-initialized')) {
        modal.setAttribute('data-report-builder-initialized', 'true');
        modal.addEventListener('shown.bs.modal', function() {
            initializeReportBuilder();
        });
        // Also initialize immediately
        setTimeout(initializeReportBuilder, 100);
    }
}

// Try to setup on DOMContentLoaded
document.addEventListener('DOMContentLoaded', setupModalListener);

// Also try immediately if DOM is already loaded
if (document.readyState !== 'loading') {
    setupModalListener();
}

// For HTMX loaded content, try after a short delay
setTimeout(setupModalListener, 200);

/**
 * Load report schema from backend
 */
function loadReportSchema() {
    fetch('/reports/api/schema/')
        .then(response => response.json())
        .then(data => {
            reportSchema = data;
            renderDataSourceOptions();
        })
        .catch(error => {
            console.error('Error loading schema:', error);
            showError('Failed to load report configuration');
        });
}

/**
 * Render data source selection buttons (checkbox-style)
 */
function renderDataSourceOptions() {
    const container = document.getElementById('dataSourceSelection');
    if (!container) {
        console.error('[Report Builder] dataSourceSelection container not found');
        return;
    }

    console.log('[Report Builder] Rendering data sources:', Object.keys(reportSchema));
    container.innerHTML = '';

    for (const [key, config] of Object.entries(reportSchema)) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline-primary data-source-btn';
        button.dataset.source = key;
        button.innerHTML = `
            <i class="${config.icon} me-2"></i>
            ${config.label}
        `;
        button.onclick = () => toggleDataSource(key);
        container.appendChild(button);
    }
    console.log('[Report Builder] Data source buttons rendered');
}

/**
 * Toggle data source selection (multi-select)
 */
function toggleDataSource(source) {
    const index = selectedDataSources.indexOf(source);
    const button = document.querySelector(`[data-source="${source}"]`);

    if (index > -1) {
        // Deselect
        selectedDataSources.splice(index, 1);
        button.classList.remove('active');
    } else {
        // Select
        selectedDataSources.push(source);
        button.classList.add('active');
    }

    console.log('[Report Builder] Selected sources:', selectedDataSources);
    updateDataSourceUI();

    if (selectedDataSources.length > 0) {
        fetchSuggestedPrimary();
    } else {
        // Hide all steps if no sources selected
        document.getElementById('primarySourceSection').classList.add('step-hidden');
        document.getElementById('step2').classList.add('step-hidden');
        document.getElementById('step3').classList.add('step-hidden');
    }
}

/**
 * Update data source UI counters
 */
function updateDataSourceUI() {
    const count = selectedDataSources.length;
    const badge = document.getElementById('selectedSourceCount');

    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.classList.remove('step-hidden');
        } else {
            badge.classList.add('step-hidden');
        }
    }

    // Store in hidden field as JSON
    const hiddenField = document.getElementById('selectedDataSources');
    if (hiddenField) {
        hiddenField.value = JSON.stringify(selectedDataSources);
    }
}

/**
 * Fetch suggested primary source from backend
 */
function fetchSuggestedPrimary() {
    fetch('/reports/api/suggest-primary/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ sources: selectedDataSources })
    })
    .then(response => response.json())
    .then(data => {
        console.log('[Report Builder] Primary source suggestion:', data);

        primarySource = data.suggested;
        document.getElementById('suggestedPrimary').textContent = reportSchema[data.suggested]?.label || data.suggested;

        // Populate primary select dropdown
        populatePrimarySelect(data.suggested, data.join_paths);

        // Show primary source section if multiple sources
        if (selectedDataSources.length > 1) {
            document.getElementById('primarySourceSection').classList.remove('step-hidden');
        } else {
            document.getElementById('primarySourceSection').classList.add('step-hidden');
        }

        // Render field selection
        renderMultiSourceFieldSelection();

        // Show next steps
        document.getElementById('step2').classList.remove('step-hidden');
        document.getElementById('step3').classList.remove('step-hidden');
    })
    .catch(error => {
        console.error('[Report Builder] Error fetching primary source:', error);
        showError('Failed to determine primary source');
    });
}

/**
 * Populate primary source select dropdown
 */
function populatePrimarySelect(suggested, joinPaths) {
    const select = document.getElementById('primarySourceSelect');
    select.innerHTML = '';

    selectedDataSources.forEach(source => {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = reportSchema[source]?.label || source;
        if (source === suggested) {
            option.selected = true;
            option.textContent += ' (Recommended)';
        }
        select.appendChild(option);
    });

    // Update on change
    select.onchange = function() {
        primarySource = this.value;
        console.log('[Report Builder] Primary source changed to:', primarySource);
        renderMultiSourceFieldSelection();
    };

    // Display join path information
    if (joinPaths && Object.keys(joinPaths).length > 0) {
        const joinInfo = document.getElementById('joinPathInfo');
        const joinList = document.getElementById('joinPathList');
        joinList.innerHTML = '';

        for (const [source, description] of Object.entries(joinPaths)) {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${reportSchema[source]?.label}</strong>: ${description}`;
            joinList.appendChild(li);
        }

        joinInfo.classList.remove('step-hidden');
    } else {
        joinInfo.classList.add('step-hidden');
    }
}

/**
 * Render field selection for multiple data sources
 */
function renderMultiSourceFieldSelection() {
    const container = document.getElementById('fieldSelection');
    if (!container) return;

    container.innerHTML = '<h6 class="mb-3">Select Fields to Include:</h6>';

    // Add "Select All" checkbox
    const selectAllDiv = document.createElement('div');
    selectAllDiv.className = 'form-check mb-3';
    selectAllDiv.innerHTML = `
        <input class="form-check-input" type="checkbox" id="selectAllFields">
        <label class="form-check-label fw-bold" for="selectAllFields">
            Select All Fields
        </label>
    `;
    container.appendChild(selectAllDiv);

    document.getElementById('selectAllFields').onchange = function() {
        const checkboxes = container.querySelectorAll('.field-checkbox');
        checkboxes.forEach(cb => cb.checked = this.checked);
        updateSelectedFields();
    };

    // Render fields grouped by data source
    selectedDataSources.forEach(source => {
        const config = reportSchema[source];
        if (!config) return;

        // Create source group
        const sourceGroup = document.createElement('div');
        sourceGroup.className = 'source-group';

        // Source header
        const header = document.createElement('div');
        header.className = 'source-group-header';
        header.innerHTML = `
            <i class="${config.icon} me-2"></i>${config.label}
            ${source === primarySource ? '<span class="badge bg-primary ms-2">Primary</span>' : ''}
        `;
        sourceGroup.appendChild(header);

        // Fields grid for this source
        const fieldsGrid = document.createElement('div');
        fieldsGrid.className = 'row';

        config.fields.forEach(field => {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-2';
            const fieldId = `field_${source}_${field.key}`;
            col.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input field-checkbox" type="checkbox"
                           value="${source}__${field.key}"
                           id="${fieldId}"
                           data-source="${source}">
                    <label class="form-check-label" for="${fieldId}">
                        ${field.label}
                        <small class="text-muted">(${field.type})</small>
                    </label>
                </div>
            `;
            fieldsGrid.appendChild(col);
        });

        sourceGroup.appendChild(fieldsGrid);
        container.appendChild(sourceGroup);
    });

    // Add change listeners
    container.querySelectorAll('.field-checkbox').forEach(checkbox => {
        checkbox.onchange = updateSelectedFields;
    });

    // Reset selected fields
    selectedFields = [];
}

/**
 * Update selected fields array
 */
function updateSelectedFields() {
    selectedFields = Array.from(document.querySelectorAll('.field-checkbox:checked'))
        .map(cb => cb.value);

    // Update field count display
    const count = selectedFields.length;
    const badge = document.getElementById('selectedFieldCount');
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.classList.remove('step-hidden');
        } else {
            badge.classList.add('step-hidden');
        }
    }

    // Enable/disable generate button
    const generateBtn = document.getElementById('generateReportBtn');
    if (generateBtn) {
        generateBtn.disabled = count === 0;
    }
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    // Preview button
    const previewBtn = document.getElementById('previewReportBtn');
    if (previewBtn) {
        previewBtn.onclick = previewReport;
    }

    // Generate button
    const generateBtn = document.getElementById('generateReportBtn');
    if (generateBtn) {
        generateBtn.onclick = generateReport;
    }

    // Reset modal on close
    const modal = document.getElementById('customReportModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', resetReportBuilder);
    }
}

/**
 * Preview report
 */
function previewReport() {
    if (selectedFields.length === 0) {
        showError('Please select at least one field');
        return;
    }

    if (selectedDataSources.length === 0) {
        showError('Please select at least one data source');
        return;
    }

    const formData = new FormData();
    formData.append('data_sources', JSON.stringify(selectedDataSources));
    formData.append('primary_source', primarySource);
    formData.append('fields', JSON.stringify(selectedFields));
    formData.append('preview', 'true');

    // Add filters
    appendFilters(formData);

    // Show loading
    const previewContainer = document.getElementById('previewContainer');
    previewContainer.classList.remove('step-hidden');
    previewContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

    fetch('/reports/api/generate-dynamic/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayPreview(data);
        } else {
            showError(data.error || 'Preview failed');
        }
    })
    .catch(error => {
        console.error('Preview error:', error);
        showError('Failed to generate preview');
    });
}

/**
 * Display preview results
 */
function displayPreview(data) {
    const container = document.getElementById('previewContainer');

    let html = `
        <div class="alert alert-info">
            <strong>Preview:</strong> ${data.record_count} records found
            <span class="float-end">Fields: ${selectedFields.length}</span>
        </div>
    `;

    if (data.preview_data && data.preview_data.length > 0) {
        html += '<div class="table-responsive"><table class="table table-sm table-bordered"><thead><tr>';

        // Headers
        const firstRecord = data.preview_data[0];
        for (const key in firstRecord) {
            html += `<th>${key}</th>`;
        }
        html += '</tr></thead><tbody>';

        // Data rows (first 5)
        data.preview_data.slice(0, 5).forEach(record => {
            html += '<tr>';
            for (const key in record) {
                html += `<td>${record[key]}</td>`;
            }
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        html += `<small class="text-muted">Showing first 5 of ${data.record_count} records</small>`;
    } else {
        html += '<p class="text-muted">No data found matching the criteria.</p>';
    }

    container.innerHTML = html;
}

/**
 * Generate full report
 */
function generateReport() {
    if (selectedFields.length === 0) {
        showError('Please select at least one field');
        return;
    }

    if (selectedDataSources.length === 0) {
        showError('Please select at least one data source');
        return;
    }

    const format = document.getElementById('outputFormat').value;

    // Create form
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/reports/api/generate-dynamic/';

    // Add fields
    form.appendChild(createHiddenInput('data_sources', JSON.stringify(selectedDataSources)));
    form.appendChild(createHiddenInput('primary_source', primarySource));
    form.appendChild(createHiddenInput('fields', JSON.stringify(selectedFields)));
    form.appendChild(createHiddenInput('format', format));
    form.appendChild(createHiddenInput('csrfmiddlewaretoken', getCookie('csrftoken')));

    // Add filters
    const formData = new FormData();
    appendFilters(formData);
    for (const [key, value] of formData.entries()) {
        if (key !== 'data_source' && key !== 'fields' && key !== 'format' && key !== 'preview') {
            form.appendChild(createHiddenInput(key, value));
        }
    }

    // Submit form
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('customReportModal'));
    modal.hide();

    showSuccess('Report is being generated...');
}

/**
 * Append filter values to FormData
 */
function appendFilters(formData) {
    const startDate = document.getElementById('filterStartDate')?.value;
    const endDate = document.getElementById('filterEndDate')?.value;

    if (startDate) formData.append('start_date', startDate);
    if (endDate) formData.append('end_date', endDate);

    // Add checkbox filters
    document.querySelectorAll('.filter-checkbox[data-filter="status"]:checked')
        .forEach(checkbox => {
            formData.append('status', checkbox.value);
        });
}

/**
 * Reset report builder to initial state
 */
function resetReportBuilder() {
    selectedDataSources = [];
    primarySource = null;
    selectedFields = [];

    document.getElementById('primarySourceSection').classList.add('step-hidden');
    document.getElementById('step2').classList.add('step-hidden');
    document.getElementById('step3').classList.add('step-hidden');
    document.getElementById('previewContainer').classList.add('step-hidden');
    document.getElementById('previewContainer').innerHTML = '';
    document.getElementById('joinPathInfo').classList.add('step-hidden');

    document.querySelectorAll('.data-source-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const badge = document.getElementById('selectedSourceCount');
    if (badge) {
        badge.classList.add('step-hidden');
    }
}

/**
 * Helper functions
 */
function createHiddenInput(name, value) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    return input;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showError(message) {
    console.error('[Report Builder Error]:', message);
    // Try to use toast if available, otherwise use alert
    if (typeof showToast === 'function') {
        showToast(message, 'error');
    } else {
        // Create a Bootstrap alert in the modal
        const modal = document.getElementById('customReportModal');
        if (modal) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show';
            alertDiv.innerHTML = `
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            modal.querySelector('.modal-body').prepend(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        } else {
            alert('Error: ' + message);
        }
    }
}

function showSuccess(message) {
    console.log('[Report Builder Success]:', message);
    if (typeof showToast === 'function') {
        showToast(message, 'success');
    } else {
        const modal = document.getElementById('customReportModal');
        if (modal) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            modal.querySelector('.modal-body').prepend(alertDiv);
            setTimeout(() => alertDiv.remove(), 3000);
        } else {
            alert(message);
        }
    }
}
