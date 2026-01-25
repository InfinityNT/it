// Reports page - Report generation and chart visualization
// Charts display device distribution, status, and assignment trends

// Global variables (use var to allow redeclaration across page scripts loaded in base.html)
var selectedReportType = '';
var currentGenerateButton = null;
var chartInstances = {};

// Color palette for charts
var chartColors = {
    primary: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69'],
    status: {
        'available': '#1cc88a',
        'assigned': '#f6c23e',
        'retired': '#858796',
        'lost': '#e74a3b',
        'damaged': '#fd7e14'
    }
};

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', initializeCharts);

function initializeCharts() {
    // Check if we're on the reports page
    if (!document.getElementById('deviceDistributionChart')) return;

    // Fetch chart data and render
    fetchChartData();
    fetchTopUsers();
}

async function fetchChartData() {
    try {
        const response = await fetch('/reports/api/charts/');
        if (!response.ok) throw new Error('Failed to fetch chart data');
        const data = await response.json();

        renderDeviceDistributionChart(data.device_distribution);
        renderStatusOverviewChart(data.status_overview);
        renderAssignmentTrendsChart(data.assignment_trends);
    } catch (error) {
        console.error('Error fetching chart data:', error);
        showChartError('deviceDistributionChart');
        showChartError('statusOverviewChart');
        showChartError('assignmentTrendsChart');
    }
}

async function fetchTopUsers() {
    try {
        const response = await fetch('/reports/api/top-users/');
        if (!response.ok) throw new Error('Failed to fetch top users');
        const data = await response.json();

        renderTopUsersTable(data);
    } catch (error) {
        console.error('Error fetching top users:', error);
        showChartError('topUsersTable');
    }
}

function renderDeviceDistributionChart(data) {
    const container = document.getElementById('deviceDistributionChart').parentElement;
    const canvas = document.getElementById('deviceDistributionChart');
    const loading = container.querySelector('.chart-loading');
    const emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    if (!data || !data.labels || data.labels.length === 0 || data.values.every(v => v === 0)) {
        emptyState.style.display = 'block';
        return;
    }

    canvas.style.display = 'block';

    // Destroy existing chart if any
    if (chartInstances.deviceDistribution) {
        chartInstances.deviceDistribution.destroy();
    }

    chartInstances.deviceDistribution = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: chartColors.primary.slice(0, data.labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, usePointStyle: true }
                }
            },
            cutout: '60%'
        }
    });
}

function renderStatusOverviewChart(data) {
    const container = document.getElementById('statusOverviewChart').parentElement;
    const canvas = document.getElementById('statusOverviewChart');
    const loading = container.querySelector('.chart-loading');
    const emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    if (!data || !data.labels || data.labels.length === 0 || data.values.every(v => v === 0)) {
        emptyState.style.display = 'block';
        return;
    }

    canvas.style.display = 'block';

    // Map status labels to colors
    const colors = data.labels.map(label => {
        const key = label.toLowerCase();
        return chartColors.status[key] || chartColors.primary[0];
    });

    if (chartInstances.statusOverview) {
        chartInstances.statusOverview.destroy();
    }

    chartInstances.statusOverview = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, usePointStyle: true }
                }
            },
            cutout: '60%'
        }
    });
}

function renderAssignmentTrendsChart(data) {
    const container = document.getElementById('assignmentTrendsChart').parentElement;
    const canvas = document.getElementById('assignmentTrendsChart');
    const loading = container.querySelector('.chart-loading');
    const emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    const hasData = data && data.labels && data.labels.length > 0 &&
        (data.assignments.some(v => v > 0) || data.returns.some(v => v > 0));

    if (!hasData) {
        emptyState.style.display = 'block';
        return;
    }

    canvas.style.display = 'block';

    if (chartInstances.assignmentTrends) {
        chartInstances.assignmentTrends.destroy();
    }

    chartInstances.assignmentTrends = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Assignments',
                    data: data.assignments,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Returns',
                    data: data.returns,
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, usePointStyle: true }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

function renderTopUsersTable(data) {
    const container = document.getElementById('topUsersTable').parentElement;
    const tableDiv = document.getElementById('topUsersTable');
    const loading = container.querySelector('.chart-loading');
    const emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    // Handle API response structure: {users: [...]}
    const users = data && data.users ? data.users : (Array.isArray(data) ? data : []);

    if (!users || users.length === 0) {
        emptyState.style.display = 'block';
        return;
    }

    tableDiv.style.display = 'block';

    let html = '<div class="table-responsive"><table class="table table-sm">';
    html += '<thead><tr><th>User</th><th class="text-end">Devices</th></tr></thead><tbody>';

    users.forEach((user, index) => {
        const badge = index < 3 ? `<span class="badge bg-${index === 0 ? 'warning' : index === 1 ? 'secondary' : 'dark'} me-2">${index + 1}</span>` : '';
        html += `<tr>
            <td>${badge}${user.name}</td>
            <td class="text-end"><span class="badge bg-primary">${user.device_count}</span></td>
        </tr>`;
    });

    html += '</tbody></table></div>';
    tableDiv.innerHTML = html;
}

function showChartError(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;

    const container = canvas.parentElement;
    const loading = container.querySelector('.chart-loading');
    const emptyState = container.querySelector('.chart-empty-state');

    if (loading) loading.style.display = 'none';
    if (emptyState) {
        emptyState.style.display = 'block';
        emptyState.querySelector('p').textContent = 'Unable to load data';
    }
}

function exportChart(chartType) {
    const chart = chartInstances[chartType === 'deviceDistribution' ? 'deviceDistribution' :
                                 chartType === 'statusOverview' ? 'statusOverview' : 'assignmentTrends'];
    if (chart) {
        const link = document.createElement('a');
        link.download = `${chartType}_chart.png`;
        link.href = chart.toBase64Image();
        link.click();
    } else {
        showAlert('warning', 'No chart data to export');
    }
}

function exportTable(tableType) {
    showAlert('info', 'Table export coming soon');
}

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
    loadingBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Generating...';
    loadingBtn.disabled = true;

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Make the request with the selected format
    fetch(`/reports/api/generate/${selectedReportType}/?format=${selectedFormat}`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
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

function exportAllReports() {
    alert('Export all reports functionality - coming soon! This will generate all reports in CSV format.');
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
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
