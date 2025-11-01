document.addEventListener('DOMContentLoaded', function() {
    // Handle form submission success
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.status === 200 && event.detail.elt.tagName === 'FORM') {
            // Form submitted successfully - redirect will be handled by server
            const spinner = document.getElementById('save-spinner');
            spinner.classList.add('d-none');
        }
    });
    
    // Handle form submission errors
    document.body.addEventListener('htmx:responseError', function(event) {
        const spinner = document.getElementById('save-spinner');
        spinner.classList.add('d-none');
        
        if (event.detail.xhr.status === 400) {
            try {
                const response = JSON.parse(event.detail.xhr.responseText);
                alert('Error: ' + (response.error || 'Please check your input and try again.'));
            } catch (e) {
                alert('An error occurred. Please check your input and try again.');
            }
        }
    });
    
    // Show spinner on form submit
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        if (event.detail.elt.tagName === 'FORM') {
            const spinner = document.getElementById('save-spinner');
            spinner.classList.remove('d-none');
        }
    });
    
    // Validate email format
    const emailInput = document.getElementById('email');
    emailInput.addEventListener('blur', function() {
        const email = this.value;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email && !emailRegex.test(email)) {
            this.setCustomValidity('Please enter a valid email address');
            this.classList.add('is-invalid');
        } else {
            this.setCustomValidity('');
            this.classList.remove('is-invalid');
        }
    });
    
    // Group change warnings
    const groupSelect = document.getElementById('groups');
    groupSelect.addEventListener('change', function() {
        const newGroupId = this.value;
        const currentHasSystemAccess = {{ user_profile.can_manage_system_settings|yesno:'true,false' }};
        
        // Check if the new group has system management permissions
        // This is a simplified check - in a real implementation you might want to
        // make an AJAX call to check the group's permissions
        const groupText = this.options[this.selectedIndex].text.toLowerCase();
        const hasSystemPerms = groupText.includes('manager') || groupText.includes('admin') || groupText.includes('system');
        
        if (hasSystemPerms && !currentHasSystemAccess) {
            if (!confirm('You are about to grant system management privileges to this user. This will give them administrative access. Continue?')) {
                this.selectedIndex = 0;
            }
        } else if (currentHasSystemAccess && !hasSystemPerms) {
            if (!confirm('You are about to remove system management privileges from this user. This will restrict their administrative access. Continue?')) {
                // Reset to first option
                this.selectedIndex = 0;
            }
        }
    });
});

function resetPassword() {
    if (confirm('Are you sure you want to reset this user\'s password? They will need to create a new password.')) {
        alert('Password reset functionality coming soon!');
    }
}

function sendWelcomeEmail() {
    if (confirm('Send welcome email to {{ user_profile.email }}?')) {
        alert('Welcome email functionality coming soon!');
    }
}

function deactivateUser() {
    if (confirm('Are you sure you want to deactivate this user account? They will not be able to log in.')) {
        const checkbox = document.getElementById('is_active');
        checkbox.checked = false;
        alert('Please save the form to apply the deactivation.');
    }
}

function activateUser() {
    if (confirm('Are you sure you want to activate this user account?')) {
        const checkbox = document.getElementById('is_active');
        checkbox.checked = true;
        alert('Please save the form to apply the activation.');
    }
}