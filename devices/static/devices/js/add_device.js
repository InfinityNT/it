// Device Add Form JavaScript
// Form validation and enhancement
// Note: Category filtering and model dropdown logic is handled inline in add_device_modal.html
// to ensure proper initialization when modal is loaded via HTMX

document.addEventListener('DOMContentLoaded', function() {
    const assetTagInput = document.getElementById('asset_tag');
    const itAssetTagInput = document.getElementById('it_asset_tag');
    const serialNumberInput = document.getElementById('serial_number');

    // Auto-uppercase asset tag (only if element exists)
    if (assetTagInput) {
        assetTagInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }

    // Auto-fill IT Asset Tag based on serial number (only if elements exist)
    if (serialNumberInput && itAssetTagInput) {
        serialNumberInput.addEventListener('input', function() {
            const serialNumber = this.value.trim();
            if (serialNumber.length >= 7) {
                const last7Chars = serialNumber.slice(-7);
                const suggestedItAssetTag = 'MEX-' + last7Chars;

                // Only auto-fill if the IT Asset Tag is empty or already follows the MEX- pattern
                if (!itAssetTagInput.value || itAssetTagInput.value.startsWith('MEX-')) {
                    itAssetTagInput.value = suggestedItAssetTag;
                }
            }
        });
    }

    // Handle form submission success
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.status === 200 && event.detail.elt.tagName === 'FORM') {
            // Form submitted successfully
            const spinner = document.getElementById('save-spinner');
            if (spinner) {
                spinner.classList.add('d-none');
            }
        }
    });

    // Handle form submission errors
    document.body.addEventListener('htmx:responseError', function(event) {
        const spinner = document.getElementById('save-spinner');
        if (spinner) {
            spinner.classList.add('d-none');
        }

        if (event.detail.xhr.status === 400) {
            try {
                const response = JSON.parse(event.detail.xhr.responseText);
                alert('Error: ' + (response.error || 'Please check your input and try again.'));
            } catch (e) {
                alert('An error occurred. Please check your input and try again.');
            }
        }
    });

    // Show spinner on form submit
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        if (event.detail.elt.tagName === 'FORM') {
            const spinner = document.getElementById('save-spinner');
            if (spinner) {
                spinner.classList.remove('d-none');
            }
        }
    });
});

// Specifications management
function addSpecification() {
    const container = document.getElementById('specifications-container');
    const newRow = document.createElement('div');
    newRow.className = 'row specification-row mt-2';
    newRow.innerHTML = `
        <div class="col-md-5">
            <select class="form-select" name="spec_key[]" onchange="updateSpecPlaceholder(this)">
                <option value="">Select specification...</option>
                <optgroup label="Hardware">
                    <option value="CPUModel">CPU Model</option>
                    <option value="GPU">Graphics Card</option>
                    <option value="RAM">Memory (RAM)</option>
                    <option value="Storage">Storage</option>
                    <option value="Display">Display</option>
                    <option value="BatteryHealth">Battery Health</option>
                    <option value="BIOSVersion">BIOS Version</option>
                </optgroup>
                <optgroup label="Software">
                    <option value="OperatingSystem">Operating System</option>
                    <option value="Firmware">Firmware Version</option>
                    <option value="Drivers">Driver Version</option>
                </optgroup>
                <optgroup label="Connectivity">
                    <option value="Ports">Ports</option>
                    <option value="WiFi">Wi-Fi</option>
                    <option value="Bluetooth">Bluetooth</option>
                    <option value="Ethernet">Ethernet</option>
                    <option value="Network">Network</option>
                </optgroup>
                <optgroup label="Physical">
                    <option value="ChassisType">Chassis Type</option>
                    <option value="FormFactor">Form Factor</option>
                    <option value="Dimensions">Dimensions</option>
                    <option value="Weight">Weight</option>
                    <option value="Color">Color</option>
                    <option value="ScreenSize">Screen Size</option>
                </optgroup>
                <optgroup label="Other">
                    <option value="SerialNumber">Serial Number</option>
                    <option value="ModelNumber">Model Number</option>
                    <option value="PartNumber">Part Number</option>
                    <option value="Capacity">Capacity</option>
                    <option value="PowerSupply">Power Supply</option>
                    <option value="Custom">Custom (type below)</option>
                </optgroup>
            </select>
        </div>
        <div class="col-md-5">
            <input type="text" class="form-control spec-value-input" name="spec_value[]" placeholder="Enter value...">
            <input type="text" class="form-control custom-spec-input d-none" name="custom_spec_key[]" placeholder="Enter custom specification name...">
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeSpecification(this)">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(newRow);
    
    // Show remove buttons for all rows except the first one
    updateRemoveButtons();
}

function removeSpecification(button) {
    const row = button.closest('.specification-row');
    row.remove();
    updateRemoveButtons();
}

function updateRemoveButtons() {
    const rows = document.querySelectorAll('.specification-row');
    rows.forEach((row, index) => {
        const removeBtn = row.querySelector('.btn-outline-danger');
        if (index === 0 && rows.length === 1) {
            removeBtn.style.display = 'none';
        } else {
            removeBtn.style.display = 'block';
        }
    });
}

// Handle specification dropdown changes
function updateSpecPlaceholder(select) {
    const row = select.closest('.specification-row');
    const valueInput = row.querySelector('.spec-value-input');
    const customInput = row.querySelector('.custom-spec-input');
    const selectedValue = select.value;
    
    // Define placeholders for each specification type
    const placeholders = {
        'CPUModel': 'e.g., Intel i7-1265U, AMD Ryzen 5 5600X',
        'GPU': 'e.g., Intel Iris Xe, NVIDIA GTX 1660, Integrated',
        'RAM': 'e.g., 16 GB DDR4, 8 GB DDR5',
        'Storage': 'e.g., 512 GB NVMe SSD, 1 TB HDD',
        'Display': 'e.g., 14" 1920x1080 IPS, 27" 4K',
        'BatteryHealth': 'e.g., 100%, 85%, Good',
        'BIOSVersion': 'e.g., 1.2.0, F4a',
        'OperatingSystem': 'e.g., Windows 11 Pro, macOS 13.1, Ubuntu 22.04',
        'Firmware': 'e.g., 1.0.2, Rev. A',
        'Drivers': 'e.g., 30.0.101.1191, Latest',
        'Ports': 'e.g., USB-C, HDMI, Ethernet, 3.5mm',
        'WiFi': 'e.g., Wi-Fi 6, 802.11ac',
        'Bluetooth': 'e.g., 5.1, 5.3',
        'Ethernet': 'e.g., Gigabit, 10/100',
        'Network': 'e.g., 5G, LTE, Wi-Fi only',
        'ChassisType': 'e.g., Laptop, Desktop, All-in-One',
        'FormFactor': 'e.g., Small Form Factor, Tower, Rack',
        'Dimensions': 'e.g., 12.3 x 8.5 x 0.6 inches',
        'Weight': 'e.g., 2.8 lbs, 1.3 kg',
        'Color': 'e.g., Space Gray, Silver, Black',
        'ScreenSize': 'e.g., 13.3", 15.6", 24"',
        'SerialNumber': 'e.g., ABC123456789',
        'ModelNumber': 'e.g., MBA13-2023, XPS-9320',
        'PartNumber': 'e.g., P/N 123-456-789',
        'Capacity': 'e.g., 500 sheets, 32 GB',
        'PowerSupply': 'e.g., 65W, 850W 80+ Gold'
    };
    
    if (selectedValue === 'Custom') {
        // Show custom input, hide value input
        valueInput.classList.add('d-none');
        customInput.classList.remove('d-none');
        customInput.focus();
    } else {
        // Show value input, hide custom input
        valueInput.classList.remove('d-none');
        customInput.classList.add('d-none');
        
        // Update placeholder
        valueInput.placeholder = placeholders[selectedValue] || 'Enter value...';
        valueInput.focus();
    }
}
