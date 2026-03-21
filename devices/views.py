from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Device, DeviceCategory, DeviceManufacturer, DeviceVendor, DeviceModel, DeviceHistory
from .serializers import (
    DeviceSerializer, DeviceCreateSerializer, DeviceCategorySerializer,
    DeviceManufacturerSerializer, DeviceVendorSerializer, DeviceModelSerializer, 
    DeviceHistorySerializer, DeviceAssignSerializer, DeviceUnassignSerializer
)
from core.models import User, Location
from employees.models import Employee
from core.decorators import permission_required_redirect


def get_spec_display_mapping():
    """Return the specification name mapping dictionary"""
    return {
        # Standardized specification names
        'CPUModel': 'CPU Model',
        'GPU': 'Graphics Card',
        'RAM': 'Memory (RAM)',
        'Storage': 'Storage',
        'Display': 'Display',
        'BatteryHealth': 'Battery Health',
        'BIOSVersion': 'BIOS Version',
        'OperatingSystem': 'Operating System',
        'Firmware': 'Firmware Version',
        'Drivers': 'Driver Version',
        'Ports': 'Ports',
        'WiFi': 'Wi-Fi',
        'Bluetooth': 'Bluetooth',
        'Ethernet': 'Ethernet',
        'Network': 'Network',
        'ChassisType': 'Chassis Type',
        'FormFactor': 'Form Factor',
        'Dimensions': 'Dimensions',
        'Weight': 'Weight',
        'Color': 'Color',
        'ScreenSize': 'Screen Size',
        'SerialNumber': 'Serial Number',
        'ModelNumber': 'Model Number',
        'PartNumber': 'Part Number',
        'Capacity': 'Capacity',
        'PowerSupply': 'Power Supply',
        
        # Legacy/common alternative names
        'cpu': 'CPU',
        'CPU': 'CPU',
        'ram': 'Memory (RAM)',
        'memory': 'Memory (RAM)',
        'storage': 'Storage',
        'hdd': 'Storage (HDD)',
        'ssd': 'Storage (SSD)',
        'gpu': 'Graphics Card',
        'graphics': 'Graphics Card',
        'display': 'Display',
        'screen': 'Screen Size',
        'wifi': 'Wi-Fi',
        'bluetooth': 'Bluetooth',
        'battery': 'Battery Health',
        'os': 'Operating System',
        'operating_system': 'Operating System',
        'bios': 'BIOS Version',
        'serial': 'Serial Number',
        'model': 'Model Number',
        'part': 'Part Number',
        'power': 'Power Supply',
        'manufacturer': 'Manufacturer',
        'brand': 'Manufacturer',
    }


def format_specifications(specifications):
    """Format specifications with proper display names"""
    if not specifications:
        return []
    
    spec_name_mapping = get_spec_display_mapping()
    formatted_specs = []
    
    for key, value in specifications.items():
        display_name = spec_name_mapping.get(key, key.replace('_', ' ').title())
        formatted_specs.append({
            'key': key,
            'display_name': display_name,
            'value': value
        })
    
    return formatted_specs


# API Views for HTML responses
@login_required
def device_list_api_view(request):
    """Device list API that returns HTML"""
    # Optimize with select_related to reduce database queries
    queryset = Device.objects.select_related(
        'device_model__category',
        'device_model',
        'assigned_to'
    )

    # Apply filters
    status_filter = request.GET.get('status')
    category = request.GET.get('category')
    search = request.GET.get('search')

    # Track if any filters are active
    has_filters = bool(status_filter or category or search)

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category:
        queryset = queryset.filter(device_model__category__name__icontains=category)
    if search:
        queryset = queryset.filter(
            models.Q(asset_tag__icontains=search) |
            models.Q(hostname__icontains=search) |
            models.Q(serial_number__icontains=search) |
            models.Q(device_model__manufacturer__icontains=search) |
            models.Q(device_model__model_name__icontains=search)
        )

    devices = queryset.order_by('asset_tag')

    # Check if database is empty (for empty state messaging)
    total_devices = Device.objects.count() if not devices.exists() else None

    context = {
        'devices': devices,
        'has_filters': has_filters,
        'is_empty_database': total_devices == 0 if total_devices is not None else False,
        'add_device_url': reverse('add-device'),
    }
    return render(request, 'components/devices/list.html', context)


# JSON API Views
class DeviceListCreateView(generics.ListCreateAPIView):
    queryset = Device.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeviceCreateSerializer
        return DeviceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category:
            queryset = queryset.filter(device_model__category__name__icontains=category)
        if search:
            queryset = queryset.filter(
                models.Q(asset_tag__icontains=search) |
                models.Q(hostname__icontains=search) |
                models.Q(serial_number__icontains=search) |
                models.Q(device_model__manufacturer__icontains=search) |
                models.Q(device_model__model_name__icontains=search)
            )
        
        return queryset.order_by('asset_tag')


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceCategoryListView(generics.ListCreateAPIView):
    queryset = DeviceCategory.objects.filter(is_active=True)
    serializer_class = DeviceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceManufacturerListView(generics.ListCreateAPIView):
    queryset = DeviceManufacturer.objects.filter(is_active=True)
    serializer_class = DeviceManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceVendorListView(generics.ListCreateAPIView):
    queryset = DeviceVendor.objects.filter(is_active=True)
    serializer_class = DeviceVendorSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceModelListView(generics.ListCreateAPIView):
    queryset = DeviceModel.objects.filter(is_active=True)
    serializer_class = DeviceModelSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_device_view(request, device_id):
    """Assign device to user (with approval workflow if needed)"""
    device = get_object_or_404(Device, id=device_id)
    
    if device.status != 'available':
        return Response({'error': 'Device is not available for assignment'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    serializer = DeviceAssignSerializer(data=request.data)
    if serializer.is_valid():
        employee_id = serializer.validated_data.get('employee_id') or serializer.validated_data.get('user_id')
        employee = Employee.objects.get(id=employee_id)
        expected_return_date = serializer.validated_data.get('expected_return_date')
        notes = serializer.validated_data.get('notes', '')
        
        # Check if assignment needs approval
        needs_approval = False
        assignment_days = 30  # Default

        # Extended assignment (over 90 days)
        if expected_return_date:
            from datetime import datetime
            try:
                return_date = datetime.strptime(expected_return_date, '%Y-%m-%d').date()
                from django.utils import timezone
                assignment_days = (return_date - timezone.now().date()).days
                if assignment_days > 90:
                    needs_approval = True
            except ValueError:
                pass

        # Permission-based approval (users without advanced assignment permissions for certain device types)
        if not request.user.has_perm('devices.can_assign_advanced_devices') and device.device_model.category.name in ['Server', 'Networking']:
            needs_approval = True

        if needs_approval:
            # Create approval request instead of direct assignment
            from approvals.views import create_approval_request

            request_data = {
                'device_id': device_id,
                'employee_id': employee_id,
                'expected_return_date': expected_return_date,
                'notes': notes,
                'assignment_days': assignment_days
            }

            title = f"Assign {device.asset_tag} to {employee.get_full_name()}"
            description = f"Request to assign device {device.asset_tag} ({device.device_model}) to {employee.get_full_name()}"
            if notes:
                description += f"\n\nNotes: {notes}"

            approval_request = create_approval_request(
                request_type='device_assignment',
                title=title,
                description=description,
                request_data=request_data,
                requested_by=request.user,
                devices=[device],
                priority='medium'
            )

            return Response({
                'message': 'Assignment request created and sent for approval',
                'approval_request_id': approval_request.id,
                'requires_approval': True
            })

        else:
            # Direct assignment without approval
            # Update device
            device.assigned_to = employee
            device.status = 'assigned'
            device.save()
            
            # Create assignment record
            from assignments.models import Assignment
            Assignment.objects.create(
                device=device,
                employee=employee,
                assigned_by=request.user,
                expected_return_date=expected_return_date,
                notes=notes
            )
            
            # Create history record
            DeviceHistory.objects.create(
                device=device,
                action='assigned',
                new_employee=employee,
                new_status='assigned',
                previous_status='available',
                notes=notes,
                created_by=request.user
            )
            
            return Response({'message': 'Device assigned successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unassign_device_view(request, device_id):
    """Unassign device from user"""
    device = get_object_or_404(Device, id=device_id)
    
    if device.status != 'assigned':
        return Response({'error': 'Device is not currently assigned'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    serializer = DeviceUnassignSerializer(data=request.data)
    if serializer.is_valid():
        previous_employee = device.assigned_to
        
        # Update device
        device.assigned_to = None
        device.status = 'available'
        device.save()

        # Update assignment record
        from assignments.models import Assignment
        assignment = Assignment.objects.filter(
            device=device,
            employee=previous_employee,
            status='active'
        ).first()

        if assignment:
            assignment.return_device(
                returned_by=request.user,
                notes=serializer.validated_data.get('notes')
            )
        
        # Create history record
        DeviceHistory.objects.create(
            device=device,
            action='unassigned',
            previous_employee=previous_employee,
            new_status='available',
            previous_status='assigned',
            notes=serializer.validated_data.get('notes', ''),
            created_by=request.user
        )
        
        return Response({'message': 'Device unassigned successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Frontend Views
@permission_required_redirect('devices.can_view_devices', message='You do not have permission to view devices.')
def devices_view(request):
    """Devices management view"""
    return render(request, 'devices/devices.html')


@login_required
def device_detail_view(request, device_id):
    """Device detail view"""
    device = get_object_or_404(Device, id=device_id)

    # Build spec label mapping from category specifications
    category = device.device_model.category
    category_specs = category.get_specification_fields() if category else []
    spec_labels = {spec.get('name'): spec.get('label', spec.get('name')) for spec in category_specs}

    # Format specifications with labels
    formatted_specs = []
    for key, value in device.device_model.specifications.items():
        if value:  # Only include non-empty specs
            formatted_specs.append({
                'key': key,
                'label': spec_labels.get(key, key),
                'value': value
            })

    context = {
        'device': device,
        'specifications': device.device_model.specifications,
        'formatted_specs': formatted_specs,
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'devices/device_detail_modal.html', context)
    # Otherwise redirect to devices page (SPA architecture)
    else:
        messages.info(request, 'Please use the device list to view device details.')
        return redirect('devices')


@login_required
def device_history_view(request, device_id):
    """Device assignment history view"""
    device = get_object_or_404(Device, id=device_id)
    
    # Get assignment history for this device
    from assignments.models import Assignment
    assignments = Assignment.objects.filter(device=device).select_related('employee', 'assigned_by', 'approved_by').order_by('-assigned_date')
    
    context = {
        'device': device,
        'assignments': assignments
    }
    messages.info(request, 'Device history is available through the device details modal.')
    return redirect('devices')


@ensure_csrf_cookie
@permission_required_redirect('devices.can_modify_devices', message='You do not have permission to add devices.')
def add_device_view(request):
    """Add new device view"""
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                from django.db import models

                # Validate category is selected
                category_name = request.POST.get('category')
                if not category_name:
                    return render(request, 'devices/add_device_modal.html', {
                        'error': 'Please select a category.',
                        'categories': DeviceCategory.objects.filter(is_active=True),
                        'device_models': DeviceModel.objects.filter(is_active=True).select_related('category'),
                    })

                # Get selected device model
                device_model_id = request.POST.get('device_model')
                if not device_model_id:
                    return render(request, 'devices/add_device_modal.html', {
                        'error': 'Please select a device model.',
                        'categories': DeviceCategory.objects.filter(is_active=True),
                        'device_models': DeviceModel.objects.filter(is_active=True).select_related('category'),
                    })
                device_model = DeviceModel.objects.select_related('category').get(id=device_model_id)

                # Validate device model category matches selected category
                if device_model.category.name != category_name:
                    return render(request, 'devices/add_device_modal.html', {
                        'error': f'Selected device model does not belong to category "{category_name}". Please select a model from the correct category.',
                        'categories': DeviceCategory.objects.filter(is_active=True),
                        'device_models': DeviceModel.objects.filter(is_active=True).select_related('category'),
                    })
                
                # Handle additional specifications (optional)
                spec_keys = request.POST.getlist('spec_key[]')
                spec_values = request.POST.getlist('spec_value[]')
                custom_spec_keys = request.POST.getlist('custom_spec_key[]')
                additional_specifications = {}
                
                for i, (key, value) in enumerate(zip(spec_keys, spec_values)):
                    if key.strip() and value.strip():
                        if key == 'Custom':
                            # Use custom specification name if provided
                            if i < len(custom_spec_keys) and custom_spec_keys[i].strip():
                                additional_specifications[custom_spec_keys[i].strip()] = value.strip()
                        else:
                            additional_specifications[key.strip()] = value.strip()
                
                # Merge additional specs with existing model specs
                if additional_specifications:
                    combined_specs = device_model.specifications.copy()
                    combined_specs.update(additional_specifications)
                    # We could save these as device-specific specs, but for now we'll just use the model specs
                
                # Extract specifications from form
                specifications = {}
                if request.POST.get('spec_cpu'):
                    specifications['CPUModel'] = request.POST.get('spec_cpu').strip()
                if request.POST.get('spec_ram'):
                    specifications['RAM'] = request.POST.get('spec_ram').strip()
                if request.POST.get('spec_storage'):
                    specifications['Storage'] = request.POST.get('spec_storage').strip()
                if request.POST.get('spec_gpu'):
                    specifications['GPU'] = request.POST.get('spec_gpu').strip()
                if request.POST.get('spec_display'):
                    specifications['Display'] = request.POST.get('spec_display').strip()
                if request.POST.get('spec_os'):
                    specifications['OperatingSystem'] = request.POST.get('spec_os').strip()

                # Update device model specifications if different
                if specifications and specifications != device_model.specifications:
                    device_model.specifications.update(specifications)
                    device_model.save()

                # Create device
                device = Device.objects.create(
                    asset_tag=request.POST.get('asset_tag'),
                    hostname=request.POST.get('hostname', ''),
                    serial_number=request.POST.get('serial_number'),
                    device_model=device_model,
                    status=request.POST.get('status', 'available'),
                    usage_type=request.POST.get('usage_type', 'individual'),
                    shared_usage=request.POST.get('shared_usage') or None,
                    ip_address=request.POST.get('ip_address') or None,
                    mac_address=request.POST.get('mac_address') or None,
                    notes=request.POST.get('notes', ''),
                    created_by=request.user
                )
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='created',
                    new_status=device.status,
                    notes=f'Device created by {request.user.get_full_name()}',
                    created_by=request.user
                )
                
                # Return success and trigger modal close + page refresh
                response = HttpResponse(status=204)  # No content - triggers hx-trigger
                response['HX-Trigger'] = 'deviceAdded'  # Custom event
                response['HX-Refresh'] = 'true'  # Refresh the page
                return response
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            # Handle regular form submission
            messages.success(request, 'Device added successfully')
            return redirect('devices')
    
    categories = DeviceCategory.objects.filter(is_active=True)
    manufacturers = DeviceManufacturer.objects.filter(is_active=True)
    vendors = DeviceVendor.objects.filter(is_active=True)
    device_models = DeviceModel.objects.filter(is_active=True).select_related('category').order_by('manufacturer', 'model_name')
    locations = Location.objects.filter(is_active=True)
    context = {
        'categories': categories,
        'manufacturers': manufacturers,
        'vendors': vendors,
        'device_models': device_models,
        'locations': locations
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'devices/add_device_modal.html', context)
    # Non-HTMX requests redirect to devices page (SPA architecture)
    else:
        messages.info(request, 'Please use the Add Device button to add new devices.')
        return redirect('devices')


@ensure_csrf_cookie
@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def edit_device_view(request, device_id):
    """Edit device view"""
    device = get_object_or_404(Device, id=device_id)
    
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                # Update ONLY the fields that are in the edit form
                # Don't touch other fields to avoid unique constraint violations
                device.asset_tag = request.POST.get('asset_tag')
                device.hostname = request.POST.get('hostname', '')
                device.serial_number = request.POST.get('serial_number')
                device.status = request.POST.get('status')
                device.notes = request.POST.get('notes', '')

                # Handle device model changes (only if provided in form)
                device_model_id = request.POST.get('device_model')
                if device_model_id and device_model_id.strip():
                    try:
                        device_model = DeviceModel.objects.get(id=int(device_model_id))
                        device.device_model = device_model
                    except (ValueError, DeviceModel.DoesNotExist):
                        pass  # Keep existing device model if invalid ID provided

                # Handle dynamic specifications from category
                category = device.device_model.category
                if category:
                    category_specs = category.get_specification_fields()
                    specifications = {}
                    for spec in category_specs:
                        spec_name = spec.get('name', '')
                        if spec_name:
                            value = request.POST.get(f'spec_{spec_name}', '').strip()
                            if value:
                                specifications[spec_name] = value
                    # Update device model specifications
                    if specifications:
                        device.device_model.specifications.update(specifications)
                        device.device_model.save()

                # Validate the device
                # Exclude device_model since it's not in the edit form
                # All other fields are either in the form or haven't been modified
                device.full_clean(exclude=['device_model'])

                print(f"Device validation passed, attempting save...")
                device.save()
                print(f"Device saved successfully: {device.id}")

                # Create history record
                print(f"Creating device history record...")
                DeviceHistory.objects.create(
                    device=device,
                    action='updated',
                    new_status=device.status,
                    notes=f'Device updated by {request.user.get_full_name()}',
                    created_by=request.user
                )
                print(f"Device history created successfully")

                # Return success and trigger modal close + page refresh
                print(f"Returning success response")
                response = HttpResponse(status=204)  # No content - triggers hx-trigger
                response['HX-Trigger'] = 'deviceUpdated'  # Custom event
                response['HX-Refresh'] = 'true'  # Refresh the page
                return response

            except ValidationError as ve:
                # Handle validation errors from full_clean()
                error_msg = []
                if hasattr(ve, 'message_dict'):
                    for field, errors in ve.message_dict.items():
                        error_msg.append(f"{field}: {', '.join(errors)}")
                else:
                    error_msg = [str(ve)]
                return JsonResponse({
                    'error': 'Validation failed',
                    'details': error_msg
                }, status=400)
            except Exception as e:
                import traceback
                error_details = {
                    'error': str(e),
                    'type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
                print(f"Edit device error: {error_details}")  # Log to console
                return JsonResponse({'error': str(e), 'type': type(e).__name__}, status=400)
        else:
            # Handle regular form submission
            messages.success(request, 'Device updated successfully')
            return redirect('device-detail-page', device_id=device.id)
    
    categories = DeviceCategory.objects.filter(is_active=True)
    manufacturers = DeviceManufacturer.objects.filter(is_active=True)
    vendors = DeviceVendor.objects.filter(is_active=True)
    device_models = DeviceModel.objects.filter(is_active=True).select_related('category').order_by('manufacturer', 'model_name')

    locations = Location.objects.filter(is_active=True)

    # Get category specifications for dynamic field rendering
    category = device.device_model.category
    category_specs = category.get_specification_fields() if category else []

    # Build spec fields with labels and current values
    spec_fields = []
    for spec in category_specs:
        name = spec.get('name', '')
        spec_fields.append({
            'name': name,
            'label': spec.get('label', name),
            'type': spec.get('type', 'text'),
            'options': spec.get('options', []),
            'value': device.device_model.specifications.get(name, ''),
        })

    context = {
        'device': device,
        'categories': categories,
        'manufacturers': manufacturers,
        'vendors': vendors,
        'device_models': device_models,
        'specifications': device.device_model.specifications,
        'spec_fields': spec_fields,
        'locations': locations,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'devices/edit_device_modal.html', context)
    else:
        messages.info(request, 'Please use the Edit button from the device list.')
        return redirect('devices')


@login_required
def advanced_search_view(request):
    """Advanced search page"""
    # If HTMX request, return content fragment
    if request.headers.get('HX-Request'):
        return render(request, 'devices/advanced_search_content.html')
    # If direct access, return full page
    else:
        return render(request, 'devices/advanced_search.html')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def advanced_search_api(request):
    """Advanced search API with filtering and export"""
    from django.core.paginator import Paginator
    from django.http import HttpResponse
    import csv
    from datetime import datetime
    
    queryset = Device.objects.select_related(
        'device_model__category',
        'device_model', 
        'assigned_to'
    ).prefetch_related('assignments')
    
    # Text search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            models.Q(asset_tag__icontains=search_query) |
            models.Q(hostname__icontains=search_query) |
            models.Q(serial_number__icontains=search_query) |
            models.Q(device_model__manufacturer__icontains=search_query) |
            models.Q(device_model__model_name__icontains=search_query) |
            models.Q(assigned_to__first_name__icontains=search_query) |
            models.Q(assigned_to__last_name__icontains=search_query) |
            models.Q(assigned_to__email__icontains=search_query) |
            models.Q(ip_address__icontains=search_query) |
            models.Q(mac_address__icontains=search_query) |
            models.Q(notes__icontains=search_query)
        )
    
    # Status filters
    status_filters = request.GET.getlist('status')
    if status_filters:
        queryset = queryset.filter(status__in=status_filters)
    
    # Category filter
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(device_model__category__name=category)
    
    # Manufacturer filter
    manufacturer = request.GET.get('manufacturer')
    if manufacturer:
        queryset = queryset.filter(device_model__manufacturer=manufacturer)

    # Date range filters
    assigned_date_from = request.GET.get('assigned_date_from')
    assigned_date_to = request.GET.get('assigned_date_to')
    if assigned_date_from:
        queryset = queryset.filter(assigned_date__gte=assigned_date_from)
    if assigned_date_to:
        queryset = queryset.filter(assigned_date__lte=assigned_date_to)
    
    # Export functionality
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="devices_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Asset Tag', 'Hostname', 'Serial Number', 'Category', 'Manufacturer', 'Model',
            'Status', 'Assigned To'
        ])

        for device in queryset:
            writer.writerow([
                device.asset_tag,
                device.hostname,
                device.serial_number,
                device.device_model.category.name,
                device.device_model.manufacturer,
                device.device_model.model_name,
                device.get_status_display(),
                device.assigned_to.get_full_name() if device.assigned_to else ''
            ])
        
        return response
    
    # Pagination
    total_count = queryset.count()
    page_size = 20
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format results
    results = []
    for device in page_obj:
        result = {
            'id': device.id,
            'asset_tag': device.asset_tag,
            'hostname': device.hostname,
            'serial_number': device.serial_number,
            'manufacturer': device.device_model.manufacturer,
            'model_name': device.device_model.model_name,
            'category': device.device_model.category.name,
            'status': device.status,
            'status_display': device.get_status_display(),
            'assigned_to': device.assigned_to.get_full_name() if device.assigned_to else None,
            'assigned_date': device.assigned_date.isoformat() if device.assigned_date else None,
        }
        results.append(result)
    
    return Response({
        'results': results,
        'total': total_count,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_size': page_size
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_model_detail_api(request, model_id):
    """API endpoint to retrieve device model with specifications"""
    try:
        model = DeviceModel.objects.get(id=model_id, is_active=True)
        serializer = DeviceModelSerializer(model)
        return Response(serializer.data)
    except DeviceModel.DoesNotExist:
        return Response({'error': 'Device model not found'}, status=404)


@login_required
def add_device_model_modal_view(request):
    """Render the add device model modal and handle form submission"""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        manufacturer = request.POST.get('manufacturer')
        model_name = request.POST.get('model_name')

        # Build specifications from form data
        specifications = {}
        for key in request.POST:
            if key.startswith('spec_'):
                spec_key = key[5:]  # Remove 'spec_' prefix
                value = request.POST.get(key, '').strip()
                if value:  # Only include non-empty specs
                    specifications[spec_key] = value

        try:
            category = DeviceCategory.objects.get(id=category_id)
            device_model = DeviceModel.objects.create(
                category=category,
                manufacturer=manufacturer,
                model_name=model_name,
                specifications=specifications
            )
            messages.success(request, f'Device model "{device_model}" created successfully.')
            # Return the updated list for the manage modal
            return manage_device_models_list_view(request)
        except DeviceCategory.DoesNotExist:
            messages.error(request, 'Invalid category selected.')
        except Exception as e:
            messages.error(request, f'Error creating device model: {str(e)}')

    # GET request - render modal
    context = {
        'categories': DeviceCategory.objects.filter(is_active=True),
        'manufacturers': DeviceManufacturer.objects.filter(is_active=True),
    }
    return render(request, 'devices/add_device_model_modal.html', context)


@login_required
def get_spec_template_view(request):
    """Return specification fields for a category via HTMX.

    Loads specifications from category.specifications (database).
    """
    category_id = request.GET.get('category')

    if not category_id:
        return render(request, 'devices/partials/spec_fields.html', {'spec_fields': [], 'category_specs': []})

    try:
        category = DeviceCategory.objects.get(id=category_id)

        # Load specifications from database
        category_specs = category.get_specification_fields()

        # Build spec_fields for backward compatibility with existing templates
        # This uses the same format as before for templates that expect tuples
        # (name, value, label)
        spec_fields = [
            (spec.get('name', ''), '', spec.get('label', spec.get('name', '')))
            for spec in category_specs
        ]

    except DeviceCategory.DoesNotExist:
        spec_fields = []
        category_specs = []

    return render(request, 'devices/partials/spec_fields.html', {
        'spec_fields': spec_fields,
        'category_specs': category_specs
    })


@login_required
def next_asset_tag_api(request, category_id):
    """API to get the next auto-generated asset tag for a category"""
    try:
        category = DeviceCategory.objects.get(id=category_id)
        asset_tag = category.generate_next_asset_tag()
        return JsonResponse({'asset_tag': asset_tag, 'prefix': category.get_asset_tag_prefix()})
    except DeviceCategory.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)


@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def add_category_modal_view(request):
    """Render the add category modal and handle form submission"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_general = request.POST.get('is_general') == 'on'

        # Build specifications list from form data
        spec_names = request.POST.getlist('spec_name[]')
        spec_labels = request.POST.getlist('spec_label[]')
        spec_types = request.POST.getlist('spec_type[]')
        spec_options = request.POST.getlist('spec_options[]')

        specifications = []
        for i, spec_name in enumerate(spec_names):
            if spec_name.strip():
                spec = {
                    'name': spec_name.strip(),
                    'type': spec_types[i] if i < len(spec_types) else 'text',
                    'label': spec_labels[i].strip() if i < len(spec_labels) and spec_labels[i].strip() else spec_name.strip()
                }
                # Add options for dropdown type
                if spec['type'] == 'dropdown' and i < len(spec_options) and spec_options[i].strip():
                    spec['options'] = [opt.strip() for opt in spec_options[i].split(',') if opt.strip()]
                specifications.append(spec)

        if not name:
            return render(request, 'devices/partials/category_add_form.html', {
                'error': 'Category name is required.',
            })

        # Check if category already exists
        if DeviceCategory.objects.filter(name__iexact=name).exists():
            return render(request, 'devices/partials/category_add_form.html', {
                'error': f'A category named "{name}" already exists.',
            })

        try:
            import json
            category = DeviceCategory.objects.create(
                name=name,
                is_general=is_general,
                specifications=specifications
            )
            # Return the full modal with toast notification
            response = render(request, 'devices/manage_categories_modal.html', {
                'can_modify': request.user.can_modify_devices,
            })
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': f'Category "{category.name}" created successfully.', 'type': 'success'}
            })
            return response
        except Exception as e:
            return render(request, 'devices/partials/category_add_form.html', {
                'error': f'Error creating category: {str(e)}',
            })

    # GET request - render add form
    return render(request, 'devices/partials/category_add_form.html')


# ==========================================
#   MANAGE CATEGORIES VIEWS
# ==========================================

@login_required
def manage_categories_view(request):
    """Render the manage categories modal"""
    return render(request, 'devices/manage_categories_modal.html', {
        'can_modify': request.user.can_modify_devices,
    })


@login_required
def manage_categories_add_form_view(request):
    """Render the add category form (replaces list view)"""
    return render(request, 'devices/partials/category_add_form.html')


@login_required
def manage_categories_list_view(request):
    """Return category list for HTMX partial updates"""
    search = request.GET.get('search', '').strip()
    categories = DeviceCategory.objects.all()

    if search:
        categories = categories.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search)
        )

    categories = categories.order_by('name')

    return render(request, 'devices/partials/category_list.html', {
        'categories': categories,
        'can_modify': request.user.can_modify_devices,
    })


@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def manage_categories_edit_view(request, category_id):
    """Edit a category with full modal takeover"""
    import json
    category = get_object_or_404(DeviceCategory, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_general = request.POST.get('is_general') == 'on'

        # Build specifications list from form data
        spec_names = request.POST.getlist('spec_name[]')
        spec_labels = request.POST.getlist('spec_label[]')
        spec_types = request.POST.getlist('spec_type[]')
        spec_options = request.POST.getlist('spec_options[]')

        specifications = []
        for i, spec_name in enumerate(spec_names):
            if spec_name.strip():
                spec = {
                    'name': spec_name.strip(),
                    'type': spec_types[i] if i < len(spec_types) else 'text',
                    'label': spec_labels[i].strip() if i < len(spec_labels) and spec_labels[i].strip() else spec_name.strip()
                }
                # Add options for dropdown type
                if spec['type'] == 'dropdown' and i < len(spec_options) and spec_options[i].strip():
                    spec['options'] = [opt.strip() for opt in spec_options[i].split(',') if opt.strip()]
                specifications.append(spec)

        if not name:
            return render(request, 'devices/partials/category_edit_form.html', {
                'category': category,
                'error': 'Category name is required.',
            })

        # Check for duplicate name (excluding current category)
        if DeviceCategory.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            return render(request, 'devices/partials/category_edit_form.html', {
                'category': category,
                'error': f'A category named "{name}" already exists.',
            })

        try:
            category.name = name
            category.is_active = is_active
            category.is_general = is_general
            category.specifications = specifications
            category.save()
            # Return the full modal with toast notification
            response = render(request, 'devices/manage_categories_modal.html', {
                'can_modify': request.user.can_modify_devices,
            })
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': f'Category "{category.name}" updated successfully.', 'type': 'success'}
            })
            return response
        except Exception as e:
            return render(request, 'devices/partials/category_edit_form.html', {
                'category': category,
                'error': f'Error updating category: {str(e)}',
            })

    # GET - return edit form
    return render(request, 'devices/partials/category_edit_form.html', {
        'category': category,
    })


@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def manage_categories_delete_view(request, category_id):
    """Delete a category with confirmation"""
    import json
    category = get_object_or_404(DeviceCategory, id=category_id)

    if request.method == 'POST':
        # Check if category has associated device models
        model_count = category.devicemodel_set.count()
        if model_count > 0:
            return render(request, 'components/common/delete_confirmation.html', {
                'item': category,
                'item_id': f'category-item-{category.id}',
                'item_name': category.name,
                'list_target_id': 'categories-list',
                'error': f'Cannot delete: {model_count} device model(s) use this category.',
                'delete_url': reverse('manage-categories-delete', args=[category_id]),
                'cancel_url': reverse('manage-categories-list'),
            })

        category_name = category.name
        category.delete()
        response = manage_categories_list_view(request)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': f'Category "{category_name}" deleted successfully.', 'type': 'success'}
        })
        return response

    # GET - return confirmation dialog
    model_count = category.devicemodel_set.count()
    return render(request, 'components/common/delete_confirmation.html', {
        'item': category,
        'item_id': f'category-item-{category.id}',
        'item_name': category.name,
        'list_target_id': 'categories-list',
        'warning': f'This category has {model_count} device model(s) associated.' if model_count else None,
        'delete_url': reverse('manage-categories-delete', args=[category_id]),
        'cancel_url': reverse('manage-categories-list'),
    })


# ==========================================
#   MANAGE DEVICE MODELS VIEWS
# ==========================================

@login_required
def manage_device_models_view(request):
    """Render the manage device models modal"""
    return render(request, 'devices/manage_device_models_modal.html', {
        'can_modify': request.user.can_modify_devices,
        'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
        'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
    })


@login_required
def manage_device_models_add_form_view(request):
    """Render the add device model form (replaces list view)"""
    return render(request, 'devices/partials/device_model_add_form.html', {
        'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
        'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
    })


@login_required
def manage_device_models_list_view(request):
    """Return device model list for HTMX partial updates"""
    search = request.GET.get('search', '').strip()
    device_models = DeviceModel.objects.select_related('category').all()

    if search:
        device_models = device_models.filter(
            models.Q(model_name__icontains=search) |
            models.Q(manufacturer__icontains=search) |
            models.Q(category__name__icontains=search)
        )

    device_models = device_models.order_by('manufacturer', 'model_name')

    return render(request, 'devices/partials/device_model_list.html', {
        'device_models': device_models,
        'can_modify': request.user.can_modify_devices,
    })


@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def manage_device_models_edit_view(request, model_id):
    """Edit a device model with full form takeover"""
    import json
    device_model = get_object_or_404(DeviceModel, id=model_id)

    def build_spec_fields(device_model, post_data=None):
        """Build spec_fields list from category spec definitions with current values."""
        category_specs = device_model.category.get_specification_fields()
        spec_fields = []
        for spec in category_specs:
            name = spec.get('name', '')
            if post_data:
                # Prefer POST data (preserving user input on error)
                value = post_data.get(f'spec_{name}', '')
            else:
                value = device_model.specifications.get(name, '') if device_model.specifications else ''
            spec_fields.append({
                'name': name,
                'label': spec.get('label', name),
                'type': spec.get('type', 'text'),
                'options': spec.get('options', []),
                'value': value,
            })
        return spec_fields

    if request.method == 'POST':
        category_id = request.POST.get('category')
        manufacturer = request.POST.get('manufacturer', '').strip()
        model_name = request.POST.get('model_name', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        errors = []
        if not category_id:
            errors.append('Category is required.')
        if not manufacturer:
            errors.append('Manufacturer is required.')
        if not model_name:
            errors.append('Model name is required.')

        if errors:
            return render(request, 'devices/partials/device_model_edit_form.html', {
                'device_model': device_model,
                'error': ' '.join(errors),
                'spec_fields': build_spec_fields(device_model, request.POST),
                'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
                'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
            })

        # Check for duplicate
        if DeviceModel.objects.filter(
            manufacturer__iexact=manufacturer,
            model_name__iexact=model_name
        ).exclude(id=model_id).exists():
            return render(request, 'devices/partials/device_model_edit_form.html', {
                'device_model': device_model,
                'error': f'A model "{manufacturer} {model_name}" already exists.',
                'spec_fields': build_spec_fields(device_model, request.POST),
                'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
                'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
            })

        try:
            device_model.category_id = category_id
            device_model.manufacturer = manufacturer
            device_model.model_name = model_name
            device_model.is_active = is_active

            # Collect specification values from form
            category = DeviceCategory.objects.get(id=category_id)
            category_specs = category.get_specification_fields()
            specifications = {}
            for spec in category_specs:
                name = spec.get('name', '')
                value = request.POST.get(f'spec_{name}', '')
                if value:
                    specifications[name] = value
            device_model.specifications = specifications

            device_model.save()
            # Return the full modal with HX-Trigger toast (matching category edit pattern)
            response = render(request, 'devices/manage_device_models_modal.html', {
                'can_modify': request.user.can_modify_devices,
                'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
                'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
            })
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': f'Device model "{device_model}" updated successfully.', 'type': 'success'}
            })
            return response
        except Exception as e:
            return render(request, 'devices/partials/device_model_edit_form.html', {
                'device_model': device_model,
                'error': f'Error updating device model: {str(e)}',
                'spec_fields': build_spec_fields(device_model, request.POST),
                'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
                'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
            })

    # GET - return edit form with spec fields pre-populated
    return render(request, 'devices/partials/device_model_edit_form.html', {
        'device_model': device_model,
        'spec_fields': build_spec_fields(device_model),
        'categories': DeviceCategory.objects.filter(is_active=True).order_by('name'),
        'manufacturers': DeviceManufacturer.objects.filter(is_active=True).order_by('name'),
    })


@login_required
@permission_required('devices.can_modify_devices', raise_exception=True)
def manage_device_models_delete_view(request, model_id):
    """Delete a device model with confirmation"""
    device_model = get_object_or_404(DeviceModel, id=model_id)

    if request.method == 'POST':
        # Check if model has associated devices
        device_count = device_model.device_set.count()
        if device_count > 0:
            return render(request, 'components/common/delete_confirmation.html', {
                'item': device_model,
                'item_id': f'device-model-item-{device_model.id}',
                'item_name': str(device_model),
                'list_target_id': 'device-models-list',
                'error': f'Cannot delete: {device_count} device(s) use this model.',
                'delete_url': reverse('manage-device-models-delete', args=[model_id]),
                'cancel_url': reverse('manage-device-models-list'),
            })

        model_name = str(device_model)
        device_model.delete()
        messages.success(request, f'Device model "{model_name}" deleted successfully.')
        return manage_device_models_list_view(request)

    # GET - return confirmation dialog
    device_count = device_model.device_set.count()
    return render(request, 'components/common/delete_confirmation.html', {
        'item': device_model,
        'item_id': f'device-model-item-{device_model.id}',
        'item_name': str(device_model),
        'list_target_id': 'device-models-list',
        'warning': f'This model has {device_count} device(s) associated.' if device_count else None,
        'delete_url': reverse('manage-device-models-delete', args=[model_id]),
        'cancel_url': reverse('manage-device-models-list'),
    })
