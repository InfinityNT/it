from django import forms
from django.contrib import admin
from .models import DeviceModel, Device, DeviceManufacturer, DeviceVendor, DeviceCategory
from core.models import Location


class DeviceModelForm(forms.ModelForm):
    """Form for creating/editing device models with required specifications"""

    # Required specifications
    spec_cpu = forms.CharField(
        label="CPU Model",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Intel Core i7-12700K, AMD Ryzen 9 5900X'
        }),
        help_text="Processor model"
    )

    spec_ram = forms.CharField(
        label="RAM",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 16 GB DDR4, 32 GB DDR5'
        }),
        help_text="Memory capacity and type"
    )

    spec_storage = forms.CharField(
        label="Storage",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 512 GB NVMe SSD, 1 TB HDD'
        }),
        help_text="Storage capacity and type"
    )

    # Optional specifications
    spec_gpu = forms.CharField(
        label="GPU (Optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., NVIDIA RTX 3080'
        })
    )

    spec_display = forms.CharField(
        label="Display (Optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 15.6" FHD (1920x1080)'
        })
    )

    spec_os = forms.CharField(
        label="Operating System (Optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Windows 11 Pro, macOS Ventura'
        })
    )

    class Meta:
        model = DeviceModel
        fields = ['category', 'manufacturer', 'model_name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate spec fields when editing
        if self.instance and self.instance.pk and self.instance.specifications:
            specs = self.instance.specifications
            self.fields['spec_cpu'].initial = specs.get('CPUModel', '')
            self.fields['spec_ram'].initial = specs.get('RAM', '')
            self.fields['spec_storage'].initial = specs.get('Storage', '')
            self.fields['spec_gpu'].initial = specs.get('GPU', '')
            self.fields['spec_display'].initial = specs.get('Display', '')
            self.fields['spec_os'].initial = specs.get('OperatingSystem', '')

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Build specifications dictionary
        instance.specifications = {
            'CPUModel': self.cleaned_data['spec_cpu'],
            'RAM': self.cleaned_data['spec_ram'],
            'Storage': self.cleaned_data['spec_storage'],
        }

        # Add optional specs if provided
        if self.cleaned_data.get('spec_gpu'):
            instance.specifications['GPU'] = self.cleaned_data['spec_gpu']
        if self.cleaned_data.get('spec_display'):
            instance.specifications['Display'] = self.cleaned_data['spec_display']
        if self.cleaned_data.get('spec_os'):
            instance.specifications['OperatingSystem'] = self.cleaned_data['spec_os']

        if commit:
            instance.save()
        return instance


class DeviceModelAdminForm(forms.ModelForm):
    """Custom admin form for DeviceModel with manufacturer dropdown"""
    
    manufacturer = forms.ModelChoiceField(
        queryset=DeviceManufacturer.objects.filter(is_active=True),
        empty_label="Select Manufacturer",
        to_field_name="name",
        help_text="Select a predefined manufacturer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = DeviceModel
        fields = '__all__'
        widgets = {
            'specifications': forms.Textarea(attrs={
                'rows': 4, 
                'cols': 50,
                'placeholder': 'Enter specifications as JSON. Example: {"CPU": "Intel i7", "RAM": "16 GB", "Storage": "512 GB SSD"}'
            }),
        }
        help_texts = {
            'specifications': 'Enter device specifications as JSON format. Common fields: CPU, RAM, Storage, Display, GPU, etc.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing model, set the manufacturer dropdown to current value
        if self.instance.pk and self.instance.manufacturer:
            try:
                manufacturer_obj = DeviceManufacturer.objects.get(name=self.instance.manufacturer)
                self.fields['manufacturer'].initial = manufacturer_obj
            except DeviceManufacturer.DoesNotExist:
                pass
    
    def save(self, commit=True):
        # Save the manufacturer name to the CharField
        instance = super().save(commit=False)
        if self.cleaned_data.get('manufacturer'):
            instance.manufacturer = self.cleaned_data['manufacturer'].name
        if commit:
            instance.save()
        return instance


class DeviceAdminForm(forms.ModelForm):
    """Custom admin form for Device with location dropdown"""

    location_choice = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        empty_label="Select Location (Optional)",
        required=False,
        help_text="Select a predefined location",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Device
        exclude = ['location']  # Exclude the original location field since we use location_choice

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing device, set the location dropdown to current value
        if self.instance.pk and self.instance.location:
            try:
                location_obj = Location.objects.get(name=self.instance.location)
                self.fields['location_choice'].initial = location_obj
            except Location.DoesNotExist:
                pass

    def save(self, commit=True):
        # Save the location name to the CharField field
        instance = super().save(commit=False)
        if self.cleaned_data.get('location_choice'):
            instance.location = self.cleaned_data['location_choice'].name
        else:
            instance.location = ''

        if commit:
            instance.save()
        return instance