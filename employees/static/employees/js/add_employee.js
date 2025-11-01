document.addEventListener('DOMContentLoaded', function() {
    const createSystemUserCheckbox = document.getElementById('create_system_user');
    const systemUserFields = document.getElementById('system-user-fields');
    const usernameField = document.getElementById('username');
    const firstNameField = document.getElementById('first_name');
    const lastNameField = document.getElementById('last_name');
    
    // Toggle system user fields
    createSystemUserCheckbox.addEventListener('change', function() {
        if (this.checked) {
            systemUserFields.classList.remove('d-none');
            // Auto-generate username from first and last name
            generateUsername();
        } else {
            systemUserFields.classList.add('d-none');
        }
    });
    
    // Auto-generate username when names change
    firstNameField.addEventListener('input', generateUsername);
    lastNameField.addEventListener('input', generateUsername);
    
    function generateUsername() {
        if (createSystemUserCheckbox.checked && firstNameField.value && lastNameField.value) {
            const username = (firstNameField.value.toLowerCase() + '.' + lastNameField.value.toLowerCase()).replace(/[^a-z.]/g, '');
            usernameField.value = username;
        }
    }
});