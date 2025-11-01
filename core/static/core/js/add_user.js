document.getElementById('groups').addEventListener('change', function() {
    const groupId = this.value;
    const groupText = this.options[this.selectedIndex].text;
    const permissionsDiv = document.getElementById('group-permissions');
    
    let permissions = '';
    
    switch(groupText) {
        case 'Viewers':
            permissions = `
                <h6>Viewers Group Permissions:</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-check text-success"></i> View devices</li>
                    <li><i class="bi bi-check text-success"></i> View employees</li>
                    <li><i class="bi bi-check text-success"></i> View assignments</li>
                    <li><i class="bi bi-check text-success"></i> View reports</li>
                    <li><i class="bi bi-x text-danger"></i> Manage devices</li>
                    <li><i class="bi bi-x text-danger"></i> Assign devices</li>
                    <li><i class="bi bi-x text-danger"></i> Manage users</li>
                    <li><i class="bi bi-x text-danger"></i> System settings</li>
                </ul>
            `;
            break;
        case 'IT_Staff':
            permissions = `
                <h6>IT Staff Group Permissions:</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-check text-success"></i> View devices</li>
                    <li><i class="bi bi-check text-success"></i> Manage devices</li>
                    <li><i class="bi bi-check text-success"></i> Assign devices</li>
                    <li><i class="bi bi-check text-success"></i> View/manage employees</li>
                    <li><i class="bi bi-check text-success"></i> Manage users</li>
                    <li><i class="bi bi-check text-success"></i> View/manage assignments</li>
                    <li><i class="bi bi-check text-success"></i> Generate reports</li>
                    <li><i class="bi bi-x text-danger"></i> System settings</li>
                    <li><i class="bi bi-x text-danger"></i> Django admin</li>
                </ul>
            `;
            break;
        case 'IT_Managers':
            permissions = `
                <h6>IT Managers Group Permissions:</h6>
                <ul class="list-unstyled">
                    <li><i class="bi bi-check text-success"></i> View devices</li>
                    <li><i class="bi bi-check text-success"></i> Manage devices</li>
                    <li><i class="bi bi-check text-success"></i> Delete devices</li>
                    <li><i class="bi bi-check text-success"></i> Assign devices</li>
                    <li><i class="bi bi-check text-success"></i> Full employee management</li>
                    <li><i class="bi bi-check text-success"></i> Full user management</li>
                    <li><i class="bi bi-check text-success"></i> Approve assignments</li>
                    <li><i class="bi bi-check text-success"></i> System settings</li>
                    <li><i class="bi bi-check text-success"></i> Django admin</li>
                    <li><i class="bi bi-check text-success"></i> Generate reports</li>
                </ul>
            `;
            break;
        default:
            permissions = '<p class="text-muted">Select a group to see permissions</p>';
    }
    
    permissionsDiv.innerHTML = permissions;
});