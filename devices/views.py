from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import models
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Device, DeviceCategory, DeviceModel, DeviceHistory
from .serializers import (
    DeviceSerializer, DeviceCreateSerializer, DeviceCategorySerializer,
    DeviceModelSerializer, DeviceHistorySerializer, DeviceAssignSerializer,
    DeviceUnassignSerializer
)
from core.models import User


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
        'PowerConsumption': 'Power Consumption',
        
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
        'power': 'Power Consumption',
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
    ).prefetch_related(
        'assignments'  # For assignment-related data
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
            models.Q(serial_number__icontains=search) |
            models.Q(device_model__manufacturer__icontains=search) |
            models.Q(device_model__model_name__icontains=search)
        )
    
    devices = queryset.order_by('asset_tag')
    context = {'devices': devices}
    return render(request, 'devices/device_list.html', context)


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
        user_id = serializer.validated_data['user_id']
        user = User.objects.get(id=user_id)
        expected_return_date = serializer.validated_data.get('expected_return_date')
        notes = serializer.validated_data.get('notes', '')
        
        # Check if assignment needs approval
        needs_approval = False
        assignment_days = 30  # Default
        
        # High-value device (over $1000)
        device_value = float(device.purchase_price) if device.purchase_price else 0
        if device_value > 1000:
            needs_approval = True
        
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
        
        # Role-based approval (non-admin users for certain device types)
        if request.user.role not in ['admin', 'manager'] and device.device_model.category.name in ['Server', 'Networking']:
            needs_approval = True
        
        if needs_approval:
            # Create approval request instead of direct assignment
            from approvals.views import create_approval_request
            
            request_data = {
                'device_id': device_id,
                'user_id': user_id,
                'expected_return_date': expected_return_date,
                'notes': notes,
                'device_value': device_value,
                'assignment_days': assignment_days
            }
            
            title = f"Assign {device.asset_tag} to {user.get_full_name()}"
            description = f"Request to assign device {device.asset_tag} ({device.device_model}) to {user.get_full_name()}"
            if notes:
                description += f"\n\nNotes: {notes}"
            
            approval_request = create_approval_request(
                request_type='device_assignment',
                title=title,
                description=description,
                request_data=request_data,
                requested_by=request.user,
                devices=[device],
                priority='high' if device_value > 1000 else 'medium'
            )
            
            return Response({
                'message': 'Assignment request created and sent for approval',
                'approval_request_id': approval_request.id,
                'requires_approval': True
            })
        
        else:
            # Direct assignment without approval
            # Update device
            device.assigned_to = user
            device.status = 'assigned'
            device.save()
            
            # Create assignment record
            from assignments.models import Assignment
            Assignment.objects.create(
                device=device,
                user=user,
                assigned_by=request.user,
                expected_return_date=expected_return_date,
                notes=notes,
                condition_at_assignment=device.condition
            )
            
            # Create history record
            DeviceHistory.objects.create(
                device=device,
                action='assigned',
                new_user=user,
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
        previous_user = device.assigned_to
        
        # Update device
        device.assigned_to = None
        device.status = 'available'
        if serializer.validated_data.get('condition'):
            device.condition = serializer.validated_data['condition']
        device.save()
        
        # Update assignment record
        from assignments.models import Assignment
        assignment = Assignment.objects.filter(
            device=device, 
            user=previous_user, 
            status='active'
        ).first()
        
        if assignment:
            assignment.return_device(
                returned_by=request.user,
                condition=serializer.validated_data.get('condition'),
                notes=serializer.validated_data.get('notes')
            )
        
        # Create history record
        DeviceHistory.objects.create(
            device=device,
            action='unassigned',
            previous_user=previous_user,
            new_status='available',
            previous_status='assigned',
            notes=serializer.validated_data.get('notes', ''),
            created_by=request.user
        )
        
        return Response({'message': 'Device unassigned successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Frontend Views
@login_required
def devices_view(request):
    """Devices management view"""
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
    return render(request, 'devices/device_detail.html', context)


@login_required
def device_history_view(request, device_id):
    """Device assignment history view"""
    device = get_object_or_404(Device, id=device_id)
    
    # Get assignment history for this device
    from assignments.models import Assignment
    assignments = Assignment.objects.filter(device=device).select_related('user', 'assigned_by', 'approved_by').order_by('-assigned_date')
    
    context = {
        'device': device,
        'assignments': assignments
    }
    return render(request, 'devices/device_history.html', context)


@ensure_csrf_cookie
@login_required
def add_device_view(request):
    """Add new device view"""
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                from django.db import models
                
                # Get or create category
                category_name = request.POST.get('category')
                category, _ = DeviceCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'{category_name} devices'}
                )
                
                # Get or create device model
                manufacturer = request.POST.get('manufacturer')
                model_name = request.POST.get('model_name')
                
                # Handle specifications
                spec_keys = request.POST.getlist('spec_key[]')
                spec_values = request.POST.getlist('spec_value[]')
                custom_spec_keys = request.POST.getlist('custom_spec_key[]')
                specifications = {}
                
                for i, (key, value) in enumerate(zip(spec_keys, spec_values)):
                    if key.strip() and value.strip():
                        if key == 'Custom':
                            # Use custom specification name if provided
                            if i < len(custom_spec_keys) and custom_spec_keys[i].strip():
                                specifications[custom_spec_keys[i].strip()] = value.strip()
                        else:
                            specifications[key.strip()] = value.strip()
                
                device_model, _ = DeviceModel.objects.get_or_create(
                    category=category,
                    manufacturer=manufacturer,
                    model_name=model_name,
                    defaults={'specifications': specifications}
                )
                
                # Create device
                device = Device.objects.create(
                    asset_tag=request.POST.get('asset_tag'),
                    serial_number=request.POST.get('serial_number'),
                    device_model=device_model,
                    status=request.POST.get('status', 'available'),
                    condition=request.POST.get('condition', 'new'),
                    purchase_date=request.POST.get('purchase_date') or None,
                    purchase_price=request.POST.get('purchase_price') or None,
                    warranty_expiry=request.POST.get('warranty_expiry') or None,
                    vendor=request.POST.get('vendor', ''),
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
                
                response = JsonResponse({'message': 'Device added successfully'})
                response['HX-Redirect'] = '/devices/'
                return response
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            # Handle regular form submission
            messages.success(request, 'Device added successfully')
            return redirect('devices')
    
    categories = DeviceCategory.objects.filter(is_active=True)
    context = {'categories': categories}
    return render(request, 'devices/add_device.html', context)


@ensure_csrf_cookie
@login_required
def edit_device_view(request, device_id):
    """Edit device view"""
    device = get_object_or_404(Device, id=device_id)
    
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                # Update basic device info
                device.asset_tag = request.POST.get('asset_tag')
                device.serial_number = request.POST.get('serial_number')
                device.status = request.POST.get('status')
                device.condition = request.POST.get('condition')
                device.purchase_date = request.POST.get('purchase_date') or None
                device.purchase_price = request.POST.get('purchase_price') or None
                device.warranty_expiry = request.POST.get('warranty_expiry') or None
                device.vendor = request.POST.get('vendor', '')
                device.location = request.POST.get('location', '')
                device.barcode = request.POST.get('barcode', '')
                device.notes = request.POST.get('notes', '')
                
                # Handle device model changes
                category_name = request.POST.get('category')
                manufacturer = request.POST.get('manufacturer')
                model_name = request.POST.get('model_name')
                
                # Get or create category
                category, _ = DeviceCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'{category_name} devices'}
                )
                
                # Handle specifications
                spec_keys = request.POST.getlist('spec_key[]')
                spec_values = request.POST.getlist('spec_value[]')
                custom_spec_keys = request.POST.getlist('custom_spec_key[]')
                specifications = {}
                
                for i, (key, value) in enumerate(zip(spec_keys, spec_values)):
                    if key.strip() and value.strip():
                        if key == 'Custom':
                            # Use custom specification name if provided
                            if i < len(custom_spec_keys) and custom_spec_keys[i].strip():
                                specifications[custom_spec_keys[i].strip()] = value.strip()
                        else:
                            specifications[key.strip()] = value.strip()
                
                # Get or create device model
                device_model, _ = DeviceModel.objects.get_or_create(
                    category=category,
                    manufacturer=manufacturer,
                    model_name=model_name,
                    defaults={'specifications': specifications}
                )
                
                # Update specifications if model already exists
                if specifications:
                    device_model.specifications = specifications
                    device_model.save()
                
                device.device_model = device_model
                device.save()
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='updated',
                    new_status=device.status,
                    notes=f'Device updated by {request.user.get_full_name()}',
                    created_by=request.user
                )
                
                response = JsonResponse({'message': 'Device updated successfully'})
                response['HX-Redirect'] = f'/devices/{device.id}/'
                return response
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            # Handle regular form submission
            messages.success(request, 'Device updated successfully')
            return redirect('device-detail-page', device_id=device.id)
    
    categories = DeviceCategory.objects.filter(is_active=True)
    formatted_specs = format_specifications(device.device_model.specifications)
    
    context = {
        'device': device,
        'categories': categories,
        'formatted_specs': formatted_specs
    }
    return render(request, 'devices/edit_device.html', context)


@login_required
def advanced_search_view(request):
    """Advanced search page"""
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
            models.Q(serial_number__icontains=search_query) |
            models.Q(device_model__manufacturer__icontains=search_query) |
            models.Q(device_model__model_name__icontains=search_query) |
            models.Q(assigned_to__first_name__icontains=search_query) |
            models.Q(assigned_to__last_name__icontains=search_query) |
            models.Q(assigned_to__email__icontains=search_query) |
            models.Q(location__icontains=search_query) |
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
    
    # Condition filter
    condition = request.GET.get('condition')
    if condition:
        queryset = queryset.filter(condition=condition)
    
    # Location filter
    location = request.GET.get('location')
    if location:
        queryset = queryset.filter(location__icontains=location)
    
    # Date range filters
    purchase_date_from = request.GET.get('purchase_date_from')
    purchase_date_to = request.GET.get('purchase_date_to')
    if purchase_date_from:
        queryset = queryset.filter(purchase_date__gte=purchase_date_from)
    if purchase_date_to:
        queryset = queryset.filter(purchase_date__lte=purchase_date_to)
    
    assigned_date_from = request.GET.get('assigned_date_from')
    assigned_date_to = request.GET.get('assigned_date_to')
    if assigned_date_from:
        queryset = queryset.filter(assigned_date__gte=assigned_date_from)
    if assigned_date_to:
        queryset = queryset.filter(assigned_date__lte=assigned_date_to)
    
    # Warranty status filter
    warranty_status = request.GET.get('warranty_status')
    if warranty_status == 'active':
        from django.utils import timezone
        queryset = queryset.filter(warranty_expiry__gt=timezone.now().date())
    elif warranty_status == 'expired':
        from django.utils import timezone
        queryset = queryset.filter(warranty_expiry__lte=timezone.now().date())
    
    # Export functionality
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="devices_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model',
            'Status', 'Condition', 'Assigned To', 'Location', 'Purchase Date',
            'Purchase Price', 'Warranty Expiry'
        ])
        
        for device in queryset:
            writer.writerow([
                device.asset_tag,
                device.serial_number,
                device.device_model.category.name,
                device.device_model.manufacturer,
                device.device_model.model_name,
                device.get_status_display(),
                device.get_condition_display(),
                device.assigned_to.get_full_name() if device.assigned_to else '',
                device.location,
                device.purchase_date.strftime('%Y-%m-%d') if device.purchase_date else '',
                f'${device.purchase_price}' if device.purchase_price else '',
                device.warranty_expiry.strftime('%Y-%m-%d') if device.warranty_expiry else ''
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
            'serial_number': device.serial_number,
            'manufacturer': device.device_model.manufacturer,
            'model_name': device.device_model.model_name,
            'category': device.device_model.category.name,
            'status': device.status,
            'status_display': device.get_status_display(),
            'condition': device.condition,
            'condition_display': device.get_condition_display(),
            'assigned_to': device.assigned_to.get_full_name() if device.assigned_to else None,
            'assigned_date': device.assigned_date.isoformat() if device.assigned_date else None,
            'location': device.location,
            'purchase_date': device.purchase_date.isoformat() if device.purchase_date else None,
            'warranty_expiry': device.warranty_expiry.isoformat() if device.warranty_expiry else None,
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
        
        elif operation == 'update_condition':
            new_condition = request.data.get('new_condition')
            if not new_condition or new_condition not in dict(Device.CONDITION_CHOICES):
                return Response({'error': 'Valid condition is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            for device in devices:
                old_condition = device.condition
                device.condition = new_condition
                device.save()
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='bulk_updated',
                    notes=f'Bulk condition update from "{old_condition}" to "{new_condition}" by {request.user.get_full_name()}',
                    created_by=request.user
                )
                updated_count += 1
        
        elif operation == 'assign_devices':
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({'error': 'User ID is required for assignment'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            try:
                assign_to_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            expected_return_date = request.data.get('expected_return_date')
            notes = request.data.get('notes', '')
            
            for device in devices:
                if device.status != 'available':
                    errors.append(f'Device {device.asset_tag} is not available for assignment')
                    continue
                
                # Update device
                device.assigned_to = assign_to_user
                device.status = 'assigned'
                device.save()
                
                # Create assignment record
                from assignments.models import Assignment
                Assignment.objects.create(
                    device=device,
                    user=assign_to_user,
                    assigned_by=request.user,
                    expected_return_date=expected_return_date,
                    notes=notes,
                    condition_at_assignment=device.condition
                )
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='assigned',
                    new_user=assign_to_user,
                    new_status='assigned',
                    previous_status='available',
                    notes=f'Bulk assignment by {request.user.get_full_name()}: {notes}',
                    created_by=request.user
                )
                updated_count += 1
        
        elif operation == 'unassign_devices':
            return_condition = request.data.get('condition')
            notes = request.data.get('notes', '')
            
            for device in devices:
                if device.status != 'assigned':
                    errors.append(f'Device {device.asset_tag} is not currently assigned')
                    continue
                
                previous_user = device.assigned_to
                
                # Update device
                device.assigned_to = None
                device.status = 'available'
                if return_condition:
                    device.condition = return_condition
                device.save()
                
                # Update assignment record
                from assignments.models import Assignment
                assignment = Assignment.objects.filter(
                    device=device,
                    user=previous_user,
                    status='active'
                ).first()
                
                if assignment:
                    assignment.return_device(
                        returned_by=request.user,
                        condition=return_condition,
                        notes=notes
                    )
                
                # Create history record
                DeviceHistory.objects.create(
                    device=device,
                    action='unassigned',
                    previous_user=previous_user,
                    new_status='available',
                    previous_status='assigned',
                    notes=f'Bulk unassignment by {request.user.get_full_name()}: {notes}',
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
