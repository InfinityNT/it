/**
 * Settings Page JavaScript
 * Handles form submissions, quick actions toggles, and system settings management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle quick actions toggle switches
    document.body.addEventListener('change', function(e) {
        if (e.target.classList.contains('action-toggle')) {
            const actionCode = e.target.dataset.actionCode;
            const isEnabled = e.target.checked;
            const label = e.target.nextElementSibling;
            const originalText = label.textContent;

            // Update the label text immediately for UX feedback
            label.textContent = isEnabled ? 'Enabled' : 'Disabled';

            // Send AJAX request to toggle action
            fetch('/api/quick-actions/toggle/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `action_code=${actionCode}&is_enabled=${isEnabled}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the quick actions sidebar without full refresh
                    const quickActionsSection = document.getElementById('quick-actions-section');
                    if (quickActionsSection) {
                        htmx.trigger(quickActionsSection, 'load');
                    }
                    showAlert('success', data.message);
                } else {
                    showAlert('danger', 'Failed to update quick action');
                    // Revert the toggle
                    e.target.checked = !isEnabled;
                    label.textContent = originalText;
                }
            })
            .catch(error => {
                console.error('Error toggling quick action:', error);
                showAlert('danger', 'An error occurred while updating quick action');
                // Revert the toggle
                e.target.checked = !isEnabled;
                label.textContent = originalText;
            });
        }
    });

    // Handle system settings form submissions
    const generalSettingsForm = document.getElementById('generalSettingsForm');
    if (generalSettingsForm) {
        generalSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings('general', this);
        });
    }

    const featureSettingsBtn = document.getElementById('saveFeatureSettings');
    if (featureSettingsBtn) {
        featureSettingsBtn.addEventListener('click', function() {
            const form = this.closest('.card-body').querySelector('form') || this.closest('.card-body');
            saveSettings('features', form);
        });
    }

    const securitySettingsBtn = document.getElementById('saveSecuritySettings');
    if (securitySettingsBtn) {
        securitySettingsBtn.addEventListener('click', function() {
            const form = this.closest('.card-body').querySelector('form') || this.closest('.card-body');
            saveSettings('security', form);
        });
    }
});

/**
 * Save settings to the backend
 */
function saveSettings(settingsType, formElement) {
    const formData = new FormData();
    formData.append('settings_type', settingsType);
    formData.append('csrfmiddlewaretoken', getCsrfToken());

    // Gather form data based on settings type
    if (settingsType === 'general') {
        formData.append('system_name', document.getElementById('systemName')?.value || '');
        formData.append('admin_email', document.getElementById('adminEmail')?.value || '');
        formData.append('timezone', document.getElementById('timezone')?.value || '');
    } else if (settingsType === 'features') {
        formData.append('enable_ldap', document.getElementById('enableLDAP')?.checked || false);
        formData.append('enable_mfa', document.getElementById('enableMFA')?.checked || false);
        formData.append('enable_barcode', document.getElementById('enableBarcode')?.checked || false);
        formData.append('enable_notifications', document.getElementById('enableNotifications')?.checked || false);
        formData.append('enable_approvals', document.getElementById('enableApprovals')?.checked || false);
    } else if (settingsType === 'security') {
        formData.append('session_timeout', document.getElementById('sessionTimeout')?.value || 30);
        formData.append('password_policy', document.getElementById('passwordPolicy')?.value || 'standard');
        formData.append('password_expiry', document.getElementById('passwordExpiry')?.value || 90);
    }

    // Show loading state
    const submitBtn = formElement.querySelector('button[type="submit"], button[type="button"]');
    const originalBtnText = submitBtn?.innerHTML;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';
    }

    // Send request
    fetch('/settings/save/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || 'Settings saved successfully');
        } else {
            showAlert('danger', data.message || 'Failed to save settings');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showAlert('danger', 'An error occurred while saving settings');
    })
    .finally(() => {
        // Restore button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    });
}

/**
 * Run backup operation
 */
function runBackup() {
    if (!confirm('Create a backup of the database now?')) {
        return;
    }

    const btn = event.target.closest('button');
    const originalBtnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Creating Backup...';

    fetch('/settings/backup/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || 'Backup created successfully');
        } else {
            showAlert('danger', data.message || 'Failed to create backup');
        }
    })
    .catch(error => {
        console.error('Error creating backup:', error);
        showAlert('danger', 'An error occurred while creating backup');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
    });
}

/**
 * Check data integrity
 */
function checkDataIntegrity() {
    if (!confirm('Check database integrity? This will scan for inconsistencies.')) {
        return;
    }

    const btn = event.target.closest('button');
    const originalBtnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Checking...';

    fetch('/settings/integrity-check/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const alertType = data.issues_found > 0 ? 'warning' : 'success';
            const message = data.issues_found > 0
                ? `Found ${data.issues_found} issue(s). ${data.message}`
                : data.message || 'No integrity issues found';
            showAlert(alertType, message);
        } else {
            showAlert('danger', data.message || 'Failed to check integrity');
        }
    })
    .catch(error => {
        console.error('Error checking integrity:', error);
        showAlert('danger', 'An error occurred during integrity check');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
    });
}

/**
 * Get CSRF token from cookie or form
 */
function getCsrfToken() {
    // Try to get from form first
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;

    // Fallback to cookie
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

/**
 * Show alert message to user
 */
function showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';
    alertDiv.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'x-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to page
    document.body.appendChild(alertDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }
    }, 5000);
}
