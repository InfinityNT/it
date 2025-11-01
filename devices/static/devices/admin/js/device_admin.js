// JavaScript for enhanced device admin forms

document.addEventListener('DOMContentLoaded', function() {
    // Add styling and functionality to admin forms
    
    // Add "Add new" links for manufacturers and vendors
    addNewModelLinks();
    
    // Add form validation
    addFormValidation();
});

function addNewModelLinks() {
    // Add quick links to add new manufacturers and vendors
    const manufacturerField = document.getElementById('id_manufacturer');
    const vendorField = document.getElementById('id_vendor');
    
    if (manufacturerField) {
        addNewLink(manufacturerField, 'Add new manufacturer', '/admin/devices/devicemanufacturer/add/');
    }
    
    if (vendorField) {
        addNewLink(vendorField, 'Add new vendor', '/admin/devices/devicevendor/add/');
    }
}

function addNewLink(field, text, url) {
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.textContent = text;
    link.style.marginLeft = '10px';
    link.style.fontSize = '12px';
    link.className = 'add-another';
    
    const fieldWrapper = field.parentNode;
    fieldWrapper.appendChild(link);
}

function addFormValidation() {
    // Add client-side validation for device model forms
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            validateDeviceModelForm(e);
        });
    }
}

function validateDeviceModelForm(e) {
    const manufacturerField = document.getElementById('id_manufacturer');
    const modelNameField = document.getElementById('id_model_name');
    
    if (manufacturerField && modelNameField) {
        if (!manufacturerField.value) {
            alert('Please select a manufacturer');
            e.preventDefault();
            return false;
        }
        
        if (!modelNameField.value.trim()) {
            alert('Please enter a model name');
            e.preventDefault();
            return false;
        }
    }
    
    return true;
}