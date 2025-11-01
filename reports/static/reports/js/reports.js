let charts = {};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChartData();
    loadTopUsers();
});

function loadChartData() {
    fetch('/reports/api/charts/', {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
        }
    })
    .then(response => response.json())
    .then(data => {
        createDeviceDistributionChart(data.device_distribution);
        createStatusOverviewChart(data.status_overview);
        createAssignmentTrendsChart(data.assignment_trends);
    })
    .catch(error => {
        console.error('Error loading chart data:', error);
    });
}

function createDeviceDistributionChart(data) {
    const ctx = document.getElementById('deviceDistributionChart').getContext('2d');
    charts.deviceDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#4e73df',
                    '#1cc88a', 
                    '#36b9cc',
                    '#f6c23e',
                    '#e74a3b',
                    '#858796',
                    '#5a5c69'
                ],
                hoverBackgroundColor: [
                    '#2e59d9',
                    '#17a673',
                    '#2c9faf',
                    '#f4b619',
                    '#c0392b',
                    '#717277',
                    '#484848'
                ],
                hoverBorderColor: "rgba(234, 236, 244, 1)",
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createStatusOverviewChart(data) {
    const ctx = document.getElementById('statusOverviewChart').getContext('2d');
    charts.statusOverview = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#1cc88a',  // Available - Green
                    '#f6c23e',  // Assigned - Yellow
                    '#36b9cc',  // Maintenance - Blue
                    '#858796',  // Retired - Gray
                ],
                hoverBackgroundColor: [
                    '#17a673',
                    '#f4b619',
                    '#2c9faf',
                    '#717277'
                ],
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createAssignmentTrendsChart(data) {
    const ctx = document.getElementById('assignmentTrendsChart').getContext('2d');
    charts.assignmentTrends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'New Assignments',
                data: data.assignments,
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                fill: true
            }, {
                label: 'Returns',
                data: data.returns,
                borderColor: '#1cc88a',
                backgroundColor: 'rgba(28, 200, 138, 0.1)',
                fill: true
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
}

function loadTopUsers() {
    fetch('/reports/api/top-users/', {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
        }
    })
    .then(response => response.json())
    .then(data => {
        displayTopUsers(data.users);
    })
    .catch(error => {
        console.error('Error loading top users:', error);
        document.getElementById('topUsersTable').innerHTML = '<p class="text-danger">Error loading data</p>';
    });
}

function displayTopUsers(users) {
    const container = document.getElementById('topUsersTable');
    
    if (users.length === 0) {
        container.innerHTML = '<p class="text-muted">No user data available</p>';
        return;
    }
    
    const html = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Devices</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>
                                <div class="d-flex align-items-center">
                                    <div class="avatar-circle me-2">
                                        <i class="bi bi-person"></i>
                                    </div>
                                    <div>
                                        <strong>${user.name}</strong><br>
                                        <small class="text-muted">${user.email}</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="badge bg-primary">${user.device_count}</span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Global variables for modal state
let selectedReportType = '';
let currentGenerateButton = null;

function generateReport(type) {
    // Store the report type and button reference
    selectedReportType = type;
    currentGenerateButton = event.target;
    
    // Update modal content
    const reportTypeDisplay = document.getElementById('selectedReportType');
    const reportNames = {
        'inventory': 'Device Inventory Report',
        'assignments': 'Assignment History Report',
        'utilization': 'Utilization Analysis',
        'maintenance': 'Maintenance Report',
        'cost': 'Cost Analysis Report',
        'user-activity': 'User Activity Report'
    };
    reportTypeDisplay.textContent = reportNames[type] || type.charAt(0).toUpperCase() + type.slice(1) + ' Report';
    
    // Reset format selection to CSV (default)
    document.getElementById('formatCSV').checked = true;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('formatSelectionModal'));
    modal.show();
}

function proceedWithDownload() {
    const selectedFormat = document.querySelector('input[name="downloadFormat"]:checked').value;
    
    // Hide the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('formatSelectionModal'));
    modal.hide();
    
    // Update button state
    const loadingBtn = currentGenerateButton;
    const originalText = loadingBtn.innerHTML;
    loadingBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Generating...';
    loadingBtn.disabled = true;
    
    // Make the request with the selected format
    fetch(`/reports/api/generate/${selectedReportType}/?format=${selectedFormat}`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Report generation failed');
    })
    .then(blob => {
        // Download the generated report
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${selectedReportType}_report_${new Date().toISOString().split('T')[0]}.${selectedFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert('success', `${selectedFormat.toUpperCase()} report generated and downloaded successfully!`);
    })
    .catch(error => {
        console.error('Error generating report:', error);
        showAlert('danger', 'Failed to generate report. Please try again.');
    })
    .finally(() => {
        loadingBtn.innerHTML = originalText;
        loadingBtn.disabled = false;
    });
}

function exportChart(chartName) {
    if (charts[chartName]) {
        const canvas = charts[chartName].canvas;
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = `${chartName}_${new Date().toISOString().split('T')[0]}.png`;
        a.click();
    }
}

function exportTable(tableName) {
    // Implementation for table export
    alert('Table export functionality would be implemented here');
}

function exportAllReports() {
    if (confirm('This will generate and download all available reports. Continue?')) {
        const reportTypes = ['inventory', 'assignments', 'utilization', 'maintenance', 'cost', 'user-activity'];
        
        reportTypes.forEach((type, index) => {
            setTimeout(() => {
                generateReport(type);
            }, index * 1000); // Stagger downloads to avoid overwhelming the server
        });
    }
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}