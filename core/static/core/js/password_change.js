document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('password-change-form');
    const newPassword1 = document.getElementById('new_password1');
    const newPassword2 = document.getElementById('new_password2');
    
    // Password confirmation validation
    function validatePasswordMatch() {
        if (newPassword1.value !== newPassword2.value) {
            newPassword2.setCustomValidity('Passwords do not match');
        } else {
            newPassword2.setCustomValidity('');
        }
    }
    
    newPassword1.addEventListener('input', validatePasswordMatch);
    newPassword2.addEventListener('input', validatePasswordMatch);
    
    // Form submission
    form.addEventListener('submit', function(e) {
        validatePasswordMatch();
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
});