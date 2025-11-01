from django.shortcuts import render, get_object_or_404, redirect
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
from core.serializers import LocationSerializer
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
    context = {'devices': devices}
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
    # If HTMX request, return content fragment
    if request.headers.get('HX-Request'):
        return render(request, 'devices/devices_content.html')
    # If direct access, return full page
    else:
        return render(request, 'devices/devices.html')


@login_required
def device_detail_view(request, device_id):
    """Device detail view"""
    device = get_object_or_404(Device, id=device_id)

    # Format specifications for display
    formatted_specs = format_specifications(device.device_model.specifications)

    context = {
        'device': device,
        'formatted_specs': formatted_specs
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
                
                # Get selected device model
                device_model_id = request.POST.get('device_model')
                device_model = DeviceModel.objects.get(id=device_model_id)
                
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
                    location=request.POST.get('location', ''),
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
    locations = Location.objects.filter(is_active=True).order_by('name')
    device_models = DeviceModel.objects.filter(is_active=True).select_related('category').order_by('manufacturer', 'model_name')
    context = {
        'categories': categories,
        'manufacturers': manufacturers,
        'vendors': vendors,
        'locations': locations,
        'device_models': device_models
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

                # Handle additional specifications (these could be device-specific)
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

                # For now, we'll just use the model's specifications
                # In the future, we could add device-specific specifications

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
    locations = Location.objects.filter(is_active=True).order_by('name')
    device_models = DeviceModel.objects.filter(is_active=True).select_related('category').order_by('manufacturer', 'model_name')
    formatted_specs = format_specifications(device.device_model.specifications)
    
    context = {
        'device': device,
        'categories': categories,
        'manufacturers': manufacturers,
        'vendors': vendors,
        'locations': locations,
        'device_models': device_models,
        'formatted_specs': formatted_specs
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
            models.Q(location__icontains=search_query) |
            models.Q(building__icontains=search_query) |
            models.Q(room__icontains=search_query) |
            models.Q(hostname__icontains=search_query) |
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

    # Location filter
    location = request.GET.get('location')
    if location:
        queryset = queryset.filter(location__icontains=location)

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
            'Status', 'Assigned To', 'Location'
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
                device.assigned_to.get_full_name() if device.assigned_to else '',
                device.location
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
            'location': device.location,
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_operations_view(request):
    """Bulk operations for devices"""
    device_ids = request.data.get('device_ids', [])
    operation = request.data.get('operation')
    
    if not device_ids or not operation:
        return Response({'error': 'Device IDs and operation are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    devices = Device.objects.filter(id__in=device_ids)
    if not devices.exists():
        return Response({'error': 'No valid devices found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    updated_count = 0
    errors = []
    
    try:
        if operation == 'update_status':
            new_status = request.data.get('new_status')
            if not new_status or new_status not in dict(Device.STATUS_CHOICES):
                return Response({'error': 'Valid status is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            for device in devices:
                # Check if status change is valid
                if device.status == 'assigned' and new_status != 'assigned':
                    # Can only change assigned devices through proper unassignment
                    errors.append(f'Device {device.asset_tag} is assigned and cannot be changed directly')
                    continue
                
                old_status = device.status
                device.status = new_status
                device.save()
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='bulk_updated',
                    new_status=new_status,
                    previous_status=old_status,
                    notes=f'Bulk status update by {request.user.get_full_name()}',
                    created_by=request.user
                )
                updated_count += 1
        
        elif operation == 'update_location':
            new_location = request.data.get('new_location', '')
            
            for device in devices:
                old_location = device.location
                device.location = new_location
                device.save()
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='bulk_updated',
                    notes=f'Bulk location update from "{old_location}" to "{new_location}" by {request.user.get_full_name()}',
                    created_by=request.user
                )
                updated_count += 1

        elif operation == 'assign_devices':
            employee_id = request.data.get('employee_id') or request.data.get('user_id')
            if not employee_id:
                return Response({'error': 'Employee ID is required for assignment'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            try:
                assign_to_employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found'}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            expected_return_date = request.data.get('expected_return_date')
            notes = request.data.get('notes', '')
            
            for device in devices:
                if device.status != 'available':
                    errors.append(f'Device {device.asset_tag} is not available for assignment')
                    continue
                
                # Update device
                device.assigned_to = assign_to_employee
                device.status = 'assigned'
                device.save()
                
                # Create assignment record
                from assignments.models import Assignment
                Assignment.objects.create(
                    device=device,
                    employee=assign_to_employee,
                    assigned_by=request.user,
                    expected_return_date=expected_return_date,
                    notes=notes
                )
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='assigned',
                    new_employee=assign_to_employee,
                    new_status='assigned',
                    previous_status='available',
                    notes=f'Bulk assignment by {request.user.get_full_name()}: {notes}',
                    created_by=request.user
                )
                updated_count += 1
        
        elif operation == 'unassign_devices':
            notes = request.data.get('notes', '')

            for device in devices:
                if device.status != 'assigned':
                    errors.append(f'Device {device.asset_tag} is not currently assigned')
                    continue

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
                        notes=notes
                    )
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='unassigned',
                    previous_employee=previous_employee,
                    new_status='available',
                    previous_status='assigned',
                    notes=f'Bulk unassignment by {request.user.get_full_name()}: {notes}',
                    created_by=request.user
                )
                updated_count += 1
        
        elif operation == 'update_specifications':
            spec_updates = request.data.get('spec_updates')
            if not spec_updates:
                return Response({'error': 'Specification updates are required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            try:
                import json
                spec_data = json.loads(spec_updates)
                if not isinstance(spec_data, dict):
                    raise ValueError("Specifications must be a JSON object")
            except (json.JSONDecodeError, ValueError) as e:
                return Response({'error': f'Invalid JSON format: {str(e)}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            for device in devices:
                # Get current specs or empty dict
                current_specs = device.device_model.specifications or {}
                
                # Merge with new specs
                updated_specs = current_specs.copy()
                updated_specs.update(spec_data)
                
                # Update device model specifications
                device.device_model.specifications = updated_specs
                device.device_model.save()
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='bulk_updated',
                    notes=f'Bulk specification update by {request.user.get_full_name()}: {spec_updates}',
                    created_by=request.user
                )
                updated_count += 1
        
        else:
            return Response({'error': 'Invalid operation'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {
            'message': f'Successfully updated {updated_count} devices',
            'updated_count': updated_count,
            'total_devices': len(device_ids)
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['error_count'] = len(errors)
        
        return Response(response_data)
    
    except Exception as e:
        return Response({'error': f'Bulk operation failed: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def location_list_api(request):
    """API endpoint for getting locations for bulk operations"""
    try:
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
