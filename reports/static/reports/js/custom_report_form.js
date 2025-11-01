document.addEventListener('DOMContentLoaded', function() {
    // Load device categories
    loadCategories();
    
    // Set default date range (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
});

function loadCategories() {
    fetch('/reports/api/categories/', {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
        }
    })
    .then(response => response.json())
    .then(data => {
        const categoryContainer = document.getElementById('category_checkboxes');
        data.forEach((category, index) => {
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6';
            
            const checkDiv = document.createElement('div');
            checkDiv.className = 'form-check';
            
            const checkbox = document.createElement('input');
            checkbox.className = 'form-check-input';
            checkbox.type = 'checkbox';
            checkbox.name = 'category_filter';
            checkbox.id = `category_${category.id}`;
            checkbox.value = category.id;
            
            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.setAttribute('for', `category_${category.id}`);
            label.innerHTML = `<i class="bi bi-tag me-2"></i>${category.name}`;
            
            checkDiv.appendChild(checkbox);
            checkDiv.appendChild(label);
            colDiv.appendChild(checkDiv);
            categoryContainer.appendChild(colDiv);
        });
    })
    .catch(error => {
        console.error('Error loading categories:', error);
    });
}

function previewReport() {
    const formData = new FormData(document.getElementById('customReportForm'));
    formData.set('preview', 'true');
    
    fetch('{% url "reports:generate-custom-report" %}', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show preview modal or open new window
            const previewWindow = window.open('', 'preview', 'width=800,height=600,scrollbars=yes');
            previewWindow.document.write(`
                <html>
                <head><title>Report Preview</title></head>
                <body>
                    <h2>Report Preview - ${data.report_type}</h2>
                    <p><strong>Records found:</strong> ${data.record_count}</p>
                    <p><strong>Date range:</strong> ${data.date_range}</p>
                    <hr>
                    <pre>${data.preview_data}</pre>
                </body>
                </html>
            `);
        } else {
            alert('Error generating preview: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error generating preview');
    });
}

// Form submission handling
document.getElementById('customReportForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Generating...';
    submitBtn.disabled = true;
    
    // Create form data and submit
    const formData = new FormData(this);
    
    fetch(this.action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Report generation failed');
    })
    .then(blob => {
        // Download the file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        const reportType = formData.get('report_type');
        const format = formData.get('output_format');
        const timestamp = new Date().toISOString().split('T')[0];
        a.download = `${reportType}_report_${timestamp}.${format}`;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success message and redirect
        alert('Report generated and downloaded successfully!');
        window.location.href = '{% url "reports:reports" %}';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to generate report. Please try again.');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
});