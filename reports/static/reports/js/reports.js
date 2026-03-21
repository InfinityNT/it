// Reports page - Report generation and chart visualization
// Charts display device distribution, status, and assignment trends
// Theme-aware: reads CSS variables, re-renders on data-theme change

// Global variables (use var to allow redeclaration across page scripts loaded in base.html)
var selectedReportType = '';
var currentGenerateButton = null;
var chartInstances = {};
var lastChartData = null;
var lastTopUsersData = null;

// ==========================================
// Theme helpers
// ==========================================

function getThemeColors() {
    var s = getComputedStyle(document.documentElement);
    var v = function(name) { return s.getPropertyValue(name).trim(); };
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        primary: v('--clr-primary'),
        success: v('--clr-success'),
        warning: v('--clr-warning'),
        danger: v('--clr-danger'),
        info: v('--clr-info'),
        textPrimary: v('--clr-text-primary'),
        textMuted: v('--clr-text-muted'),
        cardBg: v('--clr-card-bg'),
        borderColor: v('--clr-card-border'),
        surfaceSunken: v('--clr-bg-surface-sunken'),
        isDark: isDark
    };
}

function getChartPalette(count) {
    var t = getThemeColors();
    var base = [t.primary, t.success, t.info, t.warning, t.danger];
    var bgs = [];
    var borders = [];

    for (var i = 0; i < count; i++) {
        var color = base[i % base.length];
        // For items beyond the first 5, add transparency to differentiate
        if (i >= base.length) {
            var alpha = Math.max(0.4, 1 - Math.floor(i / base.length) * 0.25);
            bgs.push(hexToRgba(color, alpha));
        } else {
            bgs.push(color);
        }
        borders.push(color);
    }
    return { backgrounds: bgs, borders: borders };
}

function hexToRgba(hex, alpha) {
    // Handle rgb/rgba from CSS vars
    if (hex.startsWith('rgb')) {
        var parts = hex.match(/[\d.]+/g);
        if (parts && parts.length >= 3) {
            return 'rgba(' + parts[0] + ',' + parts[1] + ',' + parts[2] + ',' + alpha + ')';
        }
    }
    // Handle hex
    var r = 0, g = 0, b = 0;
    if (hex.length === 4) {
        r = parseInt(hex[1] + hex[1], 16);
        g = parseInt(hex[2] + hex[2], 16);
        b = parseInt(hex[3] + hex[3], 16);
    } else if (hex.length === 7) {
        r = parseInt(hex.substring(1, 3), 16);
        g = parseInt(hex.substring(3, 5), 16);
        b = parseInt(hex.substring(5, 7), 16);
    }
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
}

function applyChartDefaults(theme) {
    Chart.defaults.color = theme.textMuted;
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.color = theme.textPrimary;
    Chart.defaults.plugins.legend.labels.font = { size: 12, weight: '500' };
    Chart.defaults.plugins.tooltip.backgroundColor = theme.isDark ? 'rgba(30,41,59,0.95)' : 'rgba(0,0,0,0.8)';
    Chart.defaults.plugins.tooltip.borderColor = theme.borderColor;
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleColor = '#fff';
    Chart.defaults.plugins.tooltip.bodyColor = 'rgba(255,255,255,0.85)';
    Chart.defaults.animation.duration = 800;
    Chart.defaults.animation.easing = 'easeOutQuart';
}

// ==========================================
// Theme change observer
// ==========================================

var _themeDebounceTimer = null;

function setupThemeObserver() {
    var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].attributeName === 'data-theme') {
                clearTimeout(_themeDebounceTimer);
                _themeDebounceTimer = setTimeout(refreshAllCharts, 50);
                break;
            }
        }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

function refreshAllCharts() {
    var theme = getThemeColors();
    applyChartDefaults(theme);

    // Destroy all existing chart instances
    Object.keys(chartInstances).forEach(function(key) {
        if (chartInstances[key]) {
            chartInstances[key].destroy();
            chartInstances[key] = null;
        }
    });

    // Re-render from cached data
    if (lastChartData) {
        renderDeviceDistributionChart(lastChartData.device_distribution);
        renderStatusOverviewChart(lastChartData.status_overview);
        renderAssignmentTrendsChart(lastChartData.assignment_trends);
    }
    if (lastTopUsersData) {
        renderTopUsersTable(lastTopUsersData);
    }
}

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', initializeCharts);

function initializeCharts() {
    if (!document.getElementById('deviceDistributionChart')) return;

    var theme = getThemeColors();
    applyChartDefaults(theme);
    setupThemeObserver();

    fetchChartData();
    fetchTopUsers();
}

async function fetchChartData() {
    try {
        var response = await fetch('/reports/api/charts/');
        if (!response.ok) throw new Error('Failed to fetch chart data');
        var data = await response.json();

        lastChartData = data;
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
        var response = await fetch('/reports/api/top-users/');
        if (!response.ok) throw new Error('Failed to fetch top users');
        var data = await response.json();

        lastTopUsersData = data;
        renderTopUsersTable(data);
    } catch (error) {
        console.error('Error fetching top users:', error);
        showChartError('topUsersTable');
    }
}

// ==========================================
// Device Distribution — Doughnut with center text
// ==========================================

var centerTextPlugin = {
    id: 'centerText',
    beforeDraw: function(chart) {
        if (chart.config.type !== 'doughnut' || !chart.config.options.plugins.centerText) return;
        var ctx = chart.ctx;
        var theme = getThemeColors();
        var total = chart.data.datasets[0].data.reduce(function(a, b) { return a + b; }, 0);

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        var centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
        var centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;

        ctx.font = '700 1.5rem Inter, sans-serif';
        ctx.fillStyle = theme.textPrimary;
        ctx.fillText(total, centerX, centerY - 8);

        ctx.font = '500 0.75rem Inter, sans-serif';
        ctx.fillStyle = theme.textMuted;
        ctx.fillText('Devices', centerX, centerY + 14);
        ctx.restore();
    }
};

// Register plugin globally once
if (typeof Chart !== 'undefined') {
    Chart.register(centerTextPlugin);
}

function renderDeviceDistributionChart(data) {
    var canvas = document.getElementById('deviceDistributionChart');
    if (!canvas) return;
    var container = canvas.parentElement;
    var loading = container.querySelector('.chart-loading');
    var emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    if (!data || !data.labels || data.labels.length === 0 || data.values.every(function(v) { return v === 0; })) {
        emptyState.style.display = 'block';
        canvas.style.display = 'none';
        return;
    }

    canvas.style.display = 'block';
    emptyState.style.display = 'none';

    if (chartInstances.deviceDistribution) {
        chartInstances.deviceDistribution.destroy();
    }

    var theme = getThemeColors();
    var palette = getChartPalette(data.labels.length);

    chartInstances.deviceDistribution = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: palette.backgrounds,
                borderWidth: 2,
                borderColor: theme.cardBg,
                hoverOffset: 8,
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                centerText: true,
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'rectRounded'
                    }
                }
            }
        }
    });
}

// ==========================================
// Status Overview — Horizontal Bar
// ==========================================

function renderStatusOverviewChart(data) {
    var canvas = document.getElementById('statusOverviewChart');
    if (!canvas) return;
    var container = canvas.parentElement;
    var loading = container.querySelector('.chart-loading');
    var emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    if (!data || !data.labels || data.labels.length === 0 || data.values.every(function(v) { return v === 0; })) {
        emptyState.style.display = 'block';
        canvas.style.display = 'none';
        return;
    }

    canvas.style.display = 'block';
    emptyState.style.display = 'none';

    if (chartInstances.statusOverview) {
        chartInstances.statusOverview.destroy();
    }

    var theme = getThemeColors();
    var statusColorMap = {
        'available': theme.success,
        'assigned': theme.warning,
        'retired': theme.textMuted,
        'lost': theme.danger,
        'damaged': '#fd7e14'
    };

    // Build gradient backgrounds per bar
    var ctx = canvas.getContext('2d');
    var backgrounds = data.labels.map(function(label) {
        var color = statusColorMap[label.toLowerCase()] || theme.primary;
        var grad = ctx.createLinearGradient(0, 0, canvas.width, 0);
        grad.addColorStop(0, color);
        grad.addColorStop(1, hexToRgba(color, 0.6));
        return grad;
    });

    var borderColors = data.labels.map(function(label) {
        return statusColorMap[label.toLowerCase()] || theme.primary;
    });

    chartInstances.statusOverview = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: backgrounds,
                borderColor: borderColors,
                borderWidth: 0,
                borderRadius: 6,
                barThickness: 28
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                delay: function(ctx) {
                    return ctx.dataIndex * 100;
                }
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        color: theme.textMuted,
                        stepSize: 1
                    },
                    grid: {
                        color: hexToRgba(theme.borderColor, 0.4),
                        drawBorder: false
                    }
                },
                y: {
                    ticks: {
                        color: theme.textPrimary,
                        font: { weight: '600' }
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

// ==========================================
// Assignment Trends — Enhanced Line Chart
// ==========================================

function renderAssignmentTrendsChart(data) {
    var canvas = document.getElementById('assignmentTrendsChart');
    if (!canvas) return;
    var container = canvas.parentElement;
    var loading = container.querySelector('.chart-loading');
    var emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    var hasData = data && data.labels && data.labels.length > 0 &&
        (data.assignments.some(function(v) { return v > 0; }) || data.returns.some(function(v) { return v > 0; }));

    if (!hasData) {
        emptyState.style.display = 'block';
        canvas.style.display = 'none';
        return;
    }

    canvas.style.display = 'block';
    emptyState.style.display = 'none';

    if (chartInstances.assignmentTrends) {
        chartInstances.assignmentTrends.destroy();
    }

    var theme = getThemeColors();
    var ctx = canvas.getContext('2d');
    var height = canvas.parentElement.clientHeight || 300;

    // Vertical gradient fills
    var assignGrad = ctx.createLinearGradient(0, 0, 0, height);
    assignGrad.addColorStop(0, hexToRgba(theme.primary, 0.25));
    assignGrad.addColorStop(1, hexToRgba(theme.primary, 0));

    var returnGrad = ctx.createLinearGradient(0, 0, 0, height);
    returnGrad.addColorStop(0, hexToRgba(theme.success, 0.25));
    returnGrad.addColorStop(1, hexToRgba(theme.success, 0));

    chartInstances.assignmentTrends = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Assignments',
                    data: data.assignments,
                    borderColor: theme.primary,
                    backgroundColor: assignGrad,
                    fill: true,
                    borderWidth: 2.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: theme.primary,
                    pointHoverBorderColor: theme.cardBg,
                    pointHoverBorderWidth: 2
                },
                {
                    label: 'Returns',
                    data: data.returns,
                    borderColor: theme.success,
                    backgroundColor: returnGrad,
                    fill: true,
                    borderWidth: 2.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: theme.success,
                    pointHoverBorderColor: theme.cardBg,
                    pointHoverBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'rectRounded'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: theme.textMuted,
                        maxRotation: 0
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: theme.textMuted,
                        stepSize: 1
                    },
                    grid: {
                        color: hexToRgba(theme.borderColor, 0.4),
                        drawBorder: false
                    }
                }
            }
        }
    });
}

// ==========================================
// Top Users — Enhanced HTML list (safe DOM construction)
// ==========================================

function renderTopUsersTable(data) {
    var tableDiv = document.getElementById('topUsersTable');
    if (!tableDiv) return;
    var container = tableDiv.parentElement;
    var loading = container.querySelector('.chart-loading');
    var emptyState = container.querySelector('.chart-empty-state');

    loading.style.display = 'none';

    var users = data && data.users ? data.users : (Array.isArray(data) ? data : []);

    if (!users || users.length === 0) {
        emptyState.style.display = 'block';
        tableDiv.style.display = 'none';
        return;
    }

    tableDiv.style.display = 'block';
    emptyState.style.display = 'none';

    var maxCount = Math.max.apply(null, users.map(function(u) { return u.device_count; })) || 1;
    var rankClasses = ['rank-gold', 'rank-silver', 'rank-bronze'];

    // Build DOM safely without innerHTML
    var listEl = document.createElement('div');
    listEl.className = 'top-users-list';

    users.forEach(function(user, index) {
        var row = document.createElement('div');
        row.className = 'top-user-row';

        var rank = document.createElement('div');
        rank.className = 'top-user-rank' + (index < 3 ? ' ' + rankClasses[index] : '');
        rank.textContent = index + 1;

        var name = document.createElement('div');
        name.className = 'top-user-name';
        name.textContent = user.name;

        var barWrap = document.createElement('div');
        barWrap.className = 'top-user-bar-wrap';
        var bar = document.createElement('div');
        bar.className = 'top-user-bar';
        bar.style.width = Math.round((user.device_count / maxCount) * 100) + '%';
        barWrap.appendChild(bar);

        var count = document.createElement('div');
        count.className = 'top-user-count';
        count.textContent = user.device_count;

        row.appendChild(rank);
        row.appendChild(name);
        row.appendChild(barWrap);
        row.appendChild(count);
        listEl.appendChild(row);
    });

    tableDiv.textContent = '';
    tableDiv.appendChild(listEl);
}

// ==========================================
// Error display
// ==========================================

function showChartError(chartId) {
    var el = document.getElementById(chartId);
    if (!el) return;

    var container = el.parentElement;
    var loading = container.querySelector('.chart-loading');
    var emptyState = container.querySelector('.chart-empty-state');

    if (loading) loading.style.display = 'none';
    if (emptyState) {
        emptyState.style.display = 'block';
        var p = emptyState.querySelector('p');
        if (p) p.textContent = 'Unable to load data';
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
