/**
 * Reusable Bulk Operations Framework
 * Provides standardized bulk operations functionality across all Django apps
 */

class BulkOperationsManager {
    constructor(config) {
        this.config = {
            // Required configuration
            tableSelector: config.tableSelector,
            apiEndpoint: config.apiEndpoint,
            
            // Optional configuration with defaults
            bulkButtonId: config.bulkButtonId || 'bulkActionsBtn',
            modalId: config.modalId || 'bulkOperationsModal',
            selectAllId: config.selectAllId || 'selectAll',
            checkboxClass: config.checkboxClass || 'item-checkbox',
            bulkCellClass: config.bulkCellClass || 'bulk-select-cell',
            bulkHeaderId: config.bulkHeaderId || 'bulk-select-header',
            
            // Operation definitions
            operations: config.operations || {},
            
            // Permission checks
            permissions: config.permissions || {},
            
            // Callbacks
            onSuccess: config.onSuccess || this.defaultSuccessHandler.bind(this),
            onError: config.onError || this.defaultErrorHandler.bind(this),
            onRefresh: config.onRefresh || null
        };
        
        this.bulkMode = false;
        this.selectedItems = [];
        this.currentOperation = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateButton();
    }
    
    bindEvents() {
        // Bulk mode toggle
        const bulkBtn = document.getElementById(this.config.bulkButtonId);
        if (bulkBtn) {
            bulkBtn.addEventListener('click', () => this.toggleBulkMode());
        }
        
        // Select all checkbox
        const selectAllCheckbox = document.getElementById(this.config.selectAllId);
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', () => this.toggleSelectAll());
        }
        
        // Individual item checkboxes (delegated event handling)
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains(this.config.checkboxClass)) {
                this.updateSelection();
            }
        });
    }
    
    toggleBulkMode() {
        this.bulkMode = !this.bulkMode;
        const btn = document.getElementById(this.config.bulkButtonId);
        const header = document.getElementById(this.config.bulkHeaderId);
        const cells = document.querySelectorAll(`.${this.config.bulkCellClass}`);
        
        if (this.bulkMode) {
            btn.innerHTML = '<i class="bi bi-x"></i> Exit Bulk';
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-warning');
            if (header) header.style.display = 'table-cell';
            cells.forEach(cell => cell.style.display = 'table-cell');
        } else {
            btn.innerHTML = '<i class="bi bi-check2-square"></i> Bulk Actions';
            btn.classList.remove('btn-warning');
            btn.classList.add('btn-outline-secondary');
            if (header) header.style.display = 'none';
            cells.forEach(cell => cell.style.display = 'none');
            this.selectedItems = [];
            this.updateButton();
        }
    }
    
    toggleSelectAll() {
        const selectAll = document.getElementById(this.config.selectAllId);
        const checkboxes = document.querySelectorAll(`.${this.config.checkboxClass}`);
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
        });
        
        this.updateSelection();
    }
    
    updateSelection() {
        const checkboxes = document.querySelectorAll(`.${this.config.checkboxClass}:checked`);
        this.selectedItems = Array.from(checkboxes).map(cb => parseInt(cb.value));
        this.updateButton();
    }
    
    updateButton() {
        const btn = document.getElementById(this.config.bulkButtonId);
        if (!btn) return;
        
        if (this.selectedItems.length > 0) {
            btn.innerHTML = `<i class="bi bi-check2-square"></i> Bulk Actions (${this.selectedItems.length})`;
            btn.onclick = () => this.showOperationsModal();
        } else if (this.bulkMode) {
            btn.innerHTML = '<i class="bi bi-x"></i> Exit Bulk';
            btn.onclick = () => this.toggleBulkMode();
        }
    }
    
    showOperationsModal() {
        if (this.selectedItems.length === 0) {
            this.showAlert('warning', 'Please select items first');
            return;
        }
        
        // Update modal content
        const selectedCountElement = document.getElementById('selected-count');
        if (selectedCountElement) {
            selectedCountElement.textContent = this.selectedItems.length;
        }
        
        // Show operations menu
        this.showOperationsMenu();
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById(this.config.modalId));
        modal.show();
    }
    
    showOperationsMenu() {
        const operationsList = document.getElementById('bulk-operations-list');
        if (!operationsList) return;
        
        operationsList.innerHTML = '';
        
        Object.entries(this.config.operations).forEach(([key, operation]) => {
            // Check permissions
            if (operation.permission && !this.hasPermission(operation.permission)) {
                return;
            }
            
            const operationButton = document.createElement('button');
            operationButton.type = 'button';
            operationButton.className = 'list-group-item list-group-item-action';
            operationButton.innerHTML = `<i class="${operation.icon}"></i> ${operation.label}`;
            operationButton.onclick = () => this.showOperationForm(key);
            
            operationsList.appendChild(operationButton);
        });
        
        // Show/hide containers
        document.getElementById('bulk-operation-content').style.display = 'block';
        document.getElementById('bulk-form-container').style.display = 'none';
        document.getElementById('executeBulkBtn').style.display = 'none';
    }
    
    showOperationForm(operationKey) {
        this.currentOperation = operationKey;
        const operation = this.config.operations[operationKey];
        
        // Generate form fields
        const formFields = document.getElementById('form-fields');
        formFields.innerHTML = '';
        
        if (operation.fields) {
            operation.fields.forEach(field => {
                const fieldElement = this.createFormField(field);
                formFields.appendChild(fieldElement);
            });
        }
        
        // Show form container
        document.getElementById('bulk-operation-content').style.display = 'none';
        document.getElementById('bulk-form-container').style.display = 'block';
        document.getElementById('executeBulkBtn').style.display = 'inline-block';
        
        // Load dynamic data if needed
        if (operation.loadData) {
            operation.loadData();
        }
    }
    
    createFormField(field) {
        const div = document.createElement('div');
        div.className = 'mb-3';
        
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = field.label;
        if (field.required) {
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
        div.appendChild(label);
        
        let input;
        
        switch (field.type) {
            case 'select':
                input = document.createElement('select');
                input.className = 'form-select';
                
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = field.placeholder || `Select ${field.label.toLowerCase()}...`;
                input.appendChild(defaultOption);
                
                // Add options
                if (field.options) {
                    field.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option.value;
                        optionElement.textContent = option.label;
                        input.appendChild(optionElement);
                    });
                }
                break;
                
            case 'textarea':
                input = document.createElement('textarea');
                input.className = 'form-control';
                input.rows = field.rows || 3;
                break;
                
            case 'date':
                input = document.createElement('input');
                input.type = 'date';
                input.className = 'form-control';
                break;
                
            default:
                input = document.createElement('input');
                input.type = field.type || 'text';
                input.className = 'form-control';
                break;
        }
        
        input.name = field.name;
        if (field.placeholder) input.placeholder = field.placeholder;
        if (field.required) input.required = true;
        
        div.appendChild(input);
        
        // Add help text if provided
        if (field.helpText) {
            const helpText = document.createElement('div');
            helpText.className = 'form-text';
            helpText.textContent = field.helpText;
            div.appendChild(helpText);
        }
        
        return div;
    }
    
    backToOperationsMenu() {
        document.getElementById('bulk-operation-content').style.display = 'block';
        document.getElementById('bulk-form-container').style.display = 'none';
        document.getElementById('executeBulkBtn').style.display = 'none';
        this.currentOperation = null;
    }
    
    executeOperation() {
        if (!this.currentOperation || this.selectedItems.length === 0) {
            return;
        }
        
        const form = document.getElementById('bulkOperationForm');
        const formData = new FormData(form);
        
        // Prepare request data
        const requestData = {
            item_ids: this.selectedItems,
            operation: this.currentOperation
        };
        
        // Add form data
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                requestData[key] = value;
            }
        }
        
        // Show loading state
        const executeBtn = document.getElementById('executeBulkBtn');
        const originalText = executeBtn.innerHTML;
        executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processing...';
        executeBtn.disabled = true;
        
        // Make API call
        this.makeApiCall(requestData)
            .then(data => {
                executeBtn.innerHTML = originalText;
                executeBtn.disabled = false;
                
                if (data.message || data.success) {
                    // Close modal
                    bootstrap.Modal.getInstance(document.getElementById(this.config.modalId)).hide();
                    
                    // Handle success
                    this.config.onSuccess(data);
                    
                    // Exit bulk mode and refresh
                    this.toggleBulkMode();
                    if (this.config.onRefresh) {
                        this.config.onRefresh();
                    }
                } else {
                    this.config.onError(data.error || 'Bulk operation failed');
                }
            })
            .catch(error => {
                executeBtn.innerHTML = originalText;
                executeBtn.disabled = false;
                this.config.onError('An error occurred during bulk operation');
            });
    }
    
    makeApiCall(requestData) {
        return fetch(this.config.apiEndpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        }).then(response => response.json());
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    hasPermission(permission) {
        // Check if user has required permission
        // This should be customized based on your permission system
        if (typeof this.config.permissions[permission] === 'function') {
            return this.config.permissions[permission]();
        }
        return this.config.permissions[permission] || false;
    }
    
    defaultSuccessHandler(data) {
        let message = data.message || 'Bulk operation completed successfully';
        if (data.errors && data.errors.length > 0) {
            message += `\\n\\nWarnings:\\n${data.errors.join('\\n')}`;
        }
        this.showAlert('success', message);
    }
    
    defaultErrorHandler(errorMessage) {
        this.showAlert('danger', errorMessage);
    }
    
    showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const main = document.querySelector('main') || document.body;
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Export for use in other modules
window.BulkOperationsManager = BulkOperationsManager;