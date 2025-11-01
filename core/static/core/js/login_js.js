document.body.addEventListener('htmx:responseError', function(event) {
    if (event.detail.xhr.status === 400) {
        const response = JSON.parse(event.detail.xhr.responseText);
        let errorMessage = 'Login failed. Please check your credentials.';
        
        if (response.non_field_errors) {
            errorMessage = response.non_field_errors.join(' ');
        }
        
        // Show error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${errorMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        event.detail.target.parentNode.insertBefore(alertDiv, event.detail.target);
    }
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.status === 200 && event.target.tagName === 'FORM') {
        // Login successful, redirect to dashboard
        window.location.href = '/';
    }
});