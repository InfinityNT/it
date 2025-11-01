document.addEventListener('DOMContentLoaded', function() {
    const assignmentSelect = document.getElementById('assignment');
    const assignmentInfo = document.getElementById('assignment-info');
    const returnBtn = document.getElementById('return-btn');
    const noIssuesCheck = document.getElementById('no_issues');
    const otherChecks = document.querySelectorAll('input[name="issues"]:not(#no_issues)');
    
    // Update assignment info when assignment is selected
    assignmentSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        
        if (this.value) {
            const device = selectedOption.dataset.device;
            const employee = selectedOption.dataset.employee;
            const assignedDate = selectedOption.dataset.assignedDate;
            const expectedReturn = selectedOption.dataset.expectedReturn;
            const purpose = selectedOption.dataset.purpose;
            const condition = selectedOption.dataset.condition;
            const location = selectedOption.dataset.location;
            const isOverdue = selectedOption.dataset.overdue === 'true';
            
            assignmentInfo.innerHTML = `
                <div class="mb-2">
                    <strong>Device:</strong><br>
                    <span class="badge bg-primary">${device}</span>
                </div>
                <div class="mb-2">
                    <strong>Employee:</strong><br>
                    ${employee}
                </div>
                <div class="mb-2">
                    <strong>Assigned Date:</strong><br>
                    ${assignedDate}
                </div>
                <div class="mb-2">
                    <strong>Expected Return:</strong><br>
                    ${expectedReturn}
                    ${isOverdue ? '<span class="badge bg-danger ms-1">Overdue</span>' : ''}
                </div>
                <div class="mb-2">
                    <strong>Purpose:</strong><br>
                    ${purpose}
                </div>
                <div class="mb-2">
                    <strong>Location:</strong><br>
                    ${location}
                </div>
                <div class="mb-2">
                    <strong>Condition at Assignment:</strong><br>
                    <span class="badge bg-info">${condition}</span>
                </div>
            `;
        } else {
            assignmentInfo.innerHTML = '<p class="text-muted">Select an assignment to see details</p>';
        }
        
        updateReturnButton();
    });
    
    // Handle "No Issues" checkbox logic
    noIssuesCheck.addEventListener('change', function() {
        if (this.checked) {
            otherChecks.forEach(check => {
                check.checked = false;
                check.disabled = true;
            });
        } else {
            otherChecks.forEach(check => {
                check.disabled = false;
            });
        }
    });
    
    // Handle other issue checkboxes
    otherChecks.forEach(check => {
        check.addEventListener('change', function() {
            if (this.checked) {
                noIssuesCheck.checked = false;
            }
        });
    });
    
    // Update return button state
    function updateReturnButton() {
        const assignmentSelected = assignmentSelect.value !== '';
        const conditionSelected = document.getElementById('condition_at_return').value !== '';
        
        if (assignmentSelected && conditionSelected) {
            returnBtn.disabled = false;
            returnBtn.classList.remove('btn-secondary');
            returnBtn.classList.add('btn-warning');
        } else {
            returnBtn.disabled = true;
            returnBtn.classList.remove('btn-warning');
            returnBtn.classList.add('btn-secondary');
        }
    }
    
    // Add event listeners for required fields
    document.getElementById('condition_at_return').addEventListener('change', updateReturnButton);
    
    // Initialize button state
    updateReturnButton();
});