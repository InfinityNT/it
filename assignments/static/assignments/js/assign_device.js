document.addEventListener('DOMContentLoaded', function() {
    const deviceSelect = document.getElementById('device');
    const employeeSelect = document.getElementById('employee');
    const deviceInfo = document.getElementById('device-info');
    const employeeInfo = document.getElementById('employee-info');
    const assignBtn = document.getElementById('assign-btn');
    
    // Update device info when device is selected
    deviceSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        
        if (this.value) {
            const manufacturer = selectedOption.dataset.manufacturer;
            const model = selectedOption.dataset.model;
            const category = selectedOption.dataset.category;
            const assetTag = selectedOption.text.split(' - ')[0];
            
            deviceInfo.innerHTML = `
                <div class="mb-2">
                    <strong>Asset Tag:</strong><br>
                    <span class="badge bg-primary">${assetTag}</span>
                </div>
                <div class="mb-2">
                    <strong>Category:</strong><br>
                    <span class="badge bg-info">${category}</span>
                </div>
                <div class="mb-2">
                    <strong>Device Model:</strong><br>
                    ${manufacturer} ${model}
                </div>
            `;
        } else {
            deviceInfo.innerHTML = '<p class="text-muted">Select a device to see details</p>';
        }
        
        updateAssignButton();
    });
    
    // Update employee info when employee is selected
    employeeSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        
        if (this.value) {
            const department = selectedOption.dataset.department;
            const email = selectedOption.dataset.email;
            const employeeName = selectedOption.text.split(' - ')[1];
            const employeeId = selectedOption.text.split(' - ')[0];
            
            employeeInfo.innerHTML = `
                <div class="mb-2">
                    <strong>Employee ID:</strong><br>
                    <span class="badge bg-secondary">${employeeId}</span>
                </div>
                <div class="mb-2">
                    <strong>Name:</strong><br>
                    ${employeeName}
                </div>
                <div class="mb-2">
                    <strong>Department:</strong><br>
                    ${department}
                </div>
                <div class="mb-2">
                    <strong>Email:</strong><br>
                    <a href="mailto:${email}">${email}</a>
                </div>
            `;
        } else {
            employeeInfo.innerHTML = '<p class="text-muted">Select an employee to see details</p>';
        }
        
        updateAssignButton();
    });
    
    // Update assign button state
    function updateAssignButton() {
        const deviceSelected = deviceSelect.value !== '';
        const employeeSelected = employeeSelect.value !== '';
        const assignmentTypeSelected = document.getElementById('assignment_type').value !== '';
        
        if (deviceSelected && employeeSelected && assignmentTypeSelected) {
            assignBtn.disabled = false;
            assignBtn.classList.remove('btn-secondary');
            assignBtn.classList.add('btn-primary');
        } else {
            assignBtn.disabled = true;
            assignBtn.classList.remove('btn-primary');
            assignBtn.classList.add('btn-secondary');
        }
    }
    
    // Add event listener for assignment type
    document.getElementById('assignment_type').addEventListener('change', updateAssignButton);
    
    // Initialize button state
    updateAssignButton();
    
    // Set minimum date for expected return date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expected_return_date').min = today;
});