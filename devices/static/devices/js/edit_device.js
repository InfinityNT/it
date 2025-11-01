// Form validation and enhancement
document.addEventListener('DOMContentLoaded', function() {
    const assetTagInput = document.getElementById('asset_tag');
    const itAssetTagInput = document.getElementById('it_asset_tag');
    const serialNumberInput = document.getElementById('serial_number');
    
    // Auto-uppercase asset tag
    assetTagInput.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
    
    // Auto-fill IT Asset Tag based on serial number
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
    
    // Category filter for device models
    const categorySelect = document.getElementById('category');
    const deviceModelSelect = document.getElementById('device_model');
    const allDeviceModels = [...deviceModelSelect.options].slice(1); // Skip the first "Select" option
    
    categorySelect.addEventListener('change', function() {
        const selectedCategory = this.value;
        
        // Clear current options (except first)
        deviceModelSelect.innerHTML = '<option value="">Select Device Model</option>';
        
        // Filter and add matching device models
        allDeviceModels.forEach(option => {
            if (!selectedCategory || option.dataset.category === selectedCategory) {
                const newOption = option.cloneNode(true);
                // Preserve the selected state for the current device model
                if (option.value === '{{ device.device_model.id }}') {
                    newOption.selected = true;
                }
                deviceModelSelect.appendChild(newOption);
            }
        });
    });
    
    // Update device info when device model is selected
    deviceModelSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        
        if (this.value) {
            const manufacturer = selectedOption.dataset.manufacturer;
            const model = selectedOption.dataset.model;
            const category = selectedOption.dataset.category;
            
            // Update the category dropdown to match
            categorySelect.value = category;
        }
    });
    
    // Handle form submission success
    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.status === 200 && event.detail.elt.tagName === 'FORM') {
            // Form submitted successfully - redirect will be handled by server
            const spinner = document.getElementById('save-spinner');
            spinner.classList.add('d-none');
        }
    });
    
    // Handle form submission errors
    document.body.addEventListener('htmx:responseError', function(event) {
        const spinner = document.getElementById('save-spinner');
        spinner.classList.add('d-none');
        
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
            spinner.classList.remove('d-none');
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
            <select class="form-select" name="spec_key[]" onchange="updateSpecPlaceholderEdit(this)">
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

// Handle specification dropdown changes for edit form (preserves existing values)
function updateSpecPlaceholderEdit(select) {
    const row = select.closest('.specification-row');
    const valueInput = row.querySelector('.spec-value-input');
    const customInput = row.querySelector('.custom-spec-input');
    const selectedValue = select.value;
    
    // Preserve existing values when changing specification type in edit mode
    const currentValue = valueInput.value;
    const currentCustomKey = customInput.value;
    
    if (selectedValue === 'Custom') {
        // Show custom input, hide value input, preserve custom key if it exists
        valueInput.classList.add('d-none');
        customInput.classList.remove('d-none');
        customInput.focus();
        // Keep the existing custom key value
    } else if (selectedValue === '') {
        // Reset selection - show value input, hide custom input
        valueInput.classList.remove('d-none');
        customInput.classList.add('d-none');
        // Keep the existing value
        valueInput.focus();
    } else {
        // Standard specification selected - show value input, hide custom input
        valueInput.classList.remove('d-none');
        customInput.classList.add('d-none');
        // Keep the existing value and only update placeholder if empty
        if (!currentValue) {
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
            valueInput.placeholder = placeholders[selectedValue] || 'Enter value...';
        }
        valueInput.focus();
    }
}

// Handle specification dropdown changes for add form
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

function addCommonSpecs(type) {
    // Clear existing specifications
    const container = document.getElementById('specifications-container');
    container.innerHTML = '';
    
    let specs = [];
    
    switch(type) {
        case 'laptop':
            specs = [
                ['CPUModel', 'Intel i7-1265U'],
                ['GPU', 'Intel Iris Xe'],
                ['Display', '14" 1920x1080 IPS'],
                ['RAM', '16 GB DDR4'],
                ['Storage', '512 GB NVMe SSD'],
                ['OperatingSystem', 'Windows 11 Pro'],
                ['BatteryHealth', '100%'],
                ['BIOSVersion', '1.2.0'],
                ['Ports', 'USB-C, USB-C, HDMI, Ethernet'],
                ['WiFi', 'Wi-Fi 6'],
                ['Bluetooth', '5.1'],
                ['ChassisType', 'Laptop']
            ];
            break;
        case 'desktop':
            specs = [
                ['CPUModel', 'Intel i5-12400'],
                ['GPU', 'Intel UHD Graphics 730'],
                ['Display', 'External Required'],
                ['RAM', '16 GB DDR4'],
                ['Storage', '512 GB NVMe SSD'],
                ['OperatingSystem', 'Windows 11 Pro'],
                ['BIOSVersion', '2.1.0'],
                ['Ports', 'USB-A, USB-A, USB-C, HDMI, Ethernet'],
                ['WiFi', 'Wi-Fi 6'],
                ['Bluetooth', '5.1'],
                ['ChassisType', 'Desktop']
            ];
            break;
        case 'monitor':
            specs = [
                ['Display', '27" 2560x1440 IPS'],
                ['Ports', 'HDMI, DisplayPort, USB-C'],
                ['ChassisType', 'Monitor']
            ];
            break;
        case 'phone':
            specs = [
                ['Display', '6.1" OLED'],
                ['Storage', '256 GB'],
                ['RAM', '8 GB'],
                ['OperatingSystem', 'iOS 17'],
                ['BatteryHealth', '100%'],
                ['Ports', 'Lightning'],
                ['WiFi', 'Wi-Fi 6'],
                ['Bluetooth', '5.3'],
                ['ChassisType', 'Phone']
            ];
            break;
    }
    
    specs.forEach((spec, index) => {
        const row = document.createElement('div');
        row.className = 'row specification-row' + (index > 0 ? ' mt-2' : '');
        row.innerHTML = `
            <div class="col-md-5">
                <select class="form-select" name="spec_key[]" onchange="updateSpecPlaceholder(this)">
                    <option value="">Select specification...</option>
                    <optgroup label="Hardware">
                        <option value="CPUModel" ${spec[0] === 'CPUModel' ? 'selected' : ''}>CPU Model</option>
                        <option value="GPU" ${spec[0] === 'GPU' ? 'selected' : ''}>Graphics Card</option>
                        <option value="RAM" ${spec[0] === 'RAM' ? 'selected' : ''}>Memory (RAM)</option>
                        <option value="Storage" ${spec[0] === 'Storage' ? 'selected' : ''}>Storage</option>
                        <option value="Display" ${spec[0] === 'Display' ? 'selected' : ''}>Display</option>
                        <option value="BatteryHealth" ${spec[0] === 'BatteryHealth' ? 'selected' : ''}>Battery Health</option>
                        <option value="BIOSVersion" ${spec[0] === 'BIOSVersion' ? 'selected' : ''}>BIOS Version</option>
                    </optgroup>
                    <optgroup label="Software">
                        <option value="OperatingSystem" ${spec[0] === 'OperatingSystem' ? 'selected' : ''}>Operating System</option>
                        <option value="Firmware" ${spec[0] === 'Firmware' ? 'selected' : ''}>Firmware Version</option>
                        <option value="Drivers" ${spec[0] === 'Drivers' ? 'selected' : ''}>Driver Version</option>
                    </optgroup>
                    <optgroup label="Connectivity">
                        <option value="Ports" ${spec[0] === 'Ports' ? 'selected' : ''}>Ports</option>
                        <option value="WiFi" ${spec[0] === 'WiFi' ? 'selected' : ''}>Wi-Fi</option>
                        <option value="Bluetooth" ${spec[0] === 'Bluetooth' ? 'selected' : ''}>Bluetooth</option>
                        <option value="Ethernet" ${spec[0] === 'Ethernet' ? 'selected' : ''}>Ethernet</option>
                        <option value="Network" ${spec[0] === 'Network' ? 'selected' : ''}>Network</option>
                    </optgroup>
                    <optgroup label="Physical">
                        <option value="ChassisType" ${spec[0] === 'ChassisType' ? 'selected' : ''}>Chassis Type</option>
                        <option value="FormFactor" ${spec[0] === 'FormFactor' ? 'selected' : ''}>Form Factor</option>
                        <option value="Dimensions" ${spec[0] === 'Dimensions' ? 'selected' : ''}>Dimensions</option>
                        <option value="Weight" ${spec[0] === 'Weight' ? 'selected' : ''}>Weight</option>
                        <option value="Color" ${spec[0] === 'Color' ? 'selected' : ''}>Color</option>
                        <option value="ScreenSize" ${spec[0] === 'ScreenSize' ? 'selected' : ''}>Screen Size</option>
                    </optgroup>
                    <optgroup label="Other">
                        <option value="SerialNumber" ${spec[0] === 'SerialNumber' ? 'selected' : ''}>Serial Number</option>
                        <option value="ModelNumber" ${spec[0] === 'ModelNumber' ? 'selected' : ''}>Model Number</option>
                        <option value="PartNumber" ${spec[0] === 'PartNumber' ? 'selected' : ''}>Part Number</option>
                        <option value="Capacity" ${spec[0] === 'Capacity' ? 'selected' : ''}>Capacity</option>
                        <option value="PowerConsumption" ${spec[0] === 'PowerConsumption' ? 'selected' : ''}>Power Consumption</option>
                        <option value="Custom">Custom (type below)</option>
                    </optgroup>
                </select>
            </div>
            <div class="col-md-5">
                <input type="text" class="form-control spec-value-input" name="spec_value[]" value="${spec[1]}">
                <input type="text" class="form-control custom-spec-input d-none" name="custom_spec_key[]" placeholder="Enter custom specification name...">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeSpecification(this)" ${index === 0 && specs.length === 1 ? 'style="display: none;"' : ''}>
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        container.appendChild(row);
    });
    
    updateRemoveButtons();
}