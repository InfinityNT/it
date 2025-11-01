function returnDevice(assignmentId) {
    const modal = new bootstrap.Modal(document.getElementById('returnModal'));
    modal.show();
}

function submitReturn() {
    const form = document.getElementById('returnForm');
    const formData = new FormData(form);
    
    fetch(`/devices/api/devices/{{ assignment.device.id }}/unassign/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            condition: formData.get('condition'),
            notes: formData.get('notes')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            bootstrap.Modal.getInstance(document.getElementById('returnModal')).hide();
            location.reload(); // Refresh the page to show updated status
        } else {
            alert(data.error || 'Return failed');
        }
    })
    .catch(error => {
        alert('An error occurred during return');
        console.error('Error:', error);
    });
}