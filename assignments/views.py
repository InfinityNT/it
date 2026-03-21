from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Assignment
from .serializers import AssignmentSerializer, AssignmentListSerializer
from devices.models import Device
from employees.models import Employee
from core.models import User
from core.decorators import permission_required_redirect
from rest_framework import status
from django.db import transaction


# API Views for HTML responses
@ensure_csrf_cookie
@login_required
def assignment_list_api_view(request):
    """Assignment list API that returns HTML"""
    queryset = Assignment.objects.all()

    # Apply filters
    status_filter = request.GET.get('status')
    employee_filter = request.GET.get('employee')
    device_filter = request.GET.get('device')
    search = request.GET.get('search')

    # Track if any filters are active
    has_filters = bool(status_filter or employee_filter or device_filter or search)

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if employee_filter:
        queryset = queryset.filter(employee__id=employee_filter)
    if device_filter:
        queryset = queryset.filter(device__id=device_filter)
    if search:
        queryset = queryset.filter(
            models.Q(device__asset_tag__icontains=search) |
            models.Q(employee__first_name__icontains=search) |
            models.Q(employee__last_name__icontains=search) |
            models.Q(employee__email__icontains=search)
        )

    assignments = queryset.select_related('device', 'employee', 'assigned_by').order_by('-assigned_date')

    # Check if database is empty
    total_assignments = Assignment.objects.count() if not assignments.exists() else None

    context = {
        'assignments': assignments,
        'has_filters': has_filters,
        'is_empty_database': total_assignments == 0 if total_assignments is not None else False,
    }

    # Use different template for employee-specific assignments
    if employee_filter:
        return render(request, 'components/assignments/employee_list.html', context)
    else:
        return render(request, 'components/assignments/list.html', context)


# JSON API Views
class AssignmentListView(generics.ListAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        employee_filter = self.request.query_params.get('employee')
        device_filter = self.request.query_params.get('device')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if employee_filter:
            queryset = queryset.filter(employee__id=employee_filter)
        if device_filter:
            queryset = queryset.filter(device__id=device_filter)
        if search:
            queryset = queryset.filter(
                models.Q(device__asset_tag__icontains=search) |
                models.Q(employee__first_name__icontains=search) |
                models.Q(employee__last_name__icontains=search) |
                models.Q(employee__email__icontains=search)
            )
        
        return queryset.select_related('device', 'employee', 'assigned_by').order_by('-assigned_date')


class AssignmentDetailView(generics.RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Frontend Views
@permission_required_redirect('assignments.can_view_assignments', message='You do not have permission to view assignments.')
def assignments_view(request):
    """Assignments management view"""
    return render(request, 'assignments/assignments.html')


@login_required
def assignment_detail_view(request, assignment_id):
    """Assignment detail view"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    context = {'assignment': assignment}

    if request.headers.get('HX-Request'):
        return render(request, 'assignments/assignment_detail_modal.html', context)
    else:
        messages.info(request, 'Please use the assignment list to view details.')
        return redirect('assignments')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def return_device_view(request, device_id):
    """Return device from assignment"""
    device = get_object_or_404(Device, id=device_id)
    
    if device.status != 'assigned':
        return Response({'error': 'Device is not currently assigned'}, status=400)
    
    if not device.assigned_to:
        return Response({'error': 'Device has no active assignment'}, status=400)
    
    # Get the active assignment
    assignment = Assignment.objects.filter(
        device=device,
        employee=device.assigned_to,
        status='active'
    ).first()
    
    if not assignment:
        return Response({'error': 'No active assignment found for this device'}, status=400)

    # Get return data from request
    notes = request.data.get('notes', '')
    retire_device = request.data.get('retire_device') == '1' or request.data.get('retire_device') is True

    # Check if user needs approval for device returns
    if request.user.can_manage_system_settings:
        # Admin users can directly return devices
        assignment.return_device(
            returned_by=request.user,
            notes=notes
        )

        # Update device status based on retire_device flag
        if retire_device:
            device.status = 'retired'
        else:
            device.status = 'available'
        device.save()

        message = f'Device {device.asset_tag} returned and retired' if retire_device else f'Device {device.asset_tag} returned successfully'

        return Response({
            'message': message,
            'device_id': device.id,
            'assignment_id': assignment.id,
            'device_status': device.status
        })
    else:
        # Staff users need approval for device returns
        from approvals.views import create_approval_request

        # Build request data
        request_data = {
            'assignment_id': assignment.id,
            'device_id': device.id,
            'employee_id': assignment.employee.id,
            'return_notes': notes,
            'retire_device': retire_device
        }

        # Build description
        description = f'Request to return device {device.asset_tag} from {assignment.employee.get_full_name()}.'
        if retire_device:
            description += ' Device will be retired.'
        if notes:
            description += f' Notes: {notes}'

        # Create approval request
        approval_request = create_approval_request(
            request_type='device_return',
            title=f'Device Return Request: {device.asset_tag}',
            description=description,
            request_data=request_data,
            requested_by=request.user,
            devices=[device],
            priority='medium'
        )

        return Response({
            'message': f'Device return request submitted for approval. Request ID: {approval_request.id}',
            'approval_request_id': approval_request.id,
            'device_id': device.id,
            'assignment_id': assignment.id
        })


@login_required
def return_device_modal_view(request, device_id):
    """Return device modal content"""
    device = get_object_or_404(Device, id=device_id)

    if device.status != 'assigned' or not device.assigned_to:
        return JsonResponse({'error': 'Device is not currently assigned'}, status=400)

    # Get the active assignment
    assignment = Assignment.objects.filter(
        device=device,
        employee=device.assigned_to,
        status='active'
    ).first()

    context = {
        'device': device,
        'device_id': device.id,  # Add device_id for template URL tag
        'assignment': assignment
    }
    return render(request, 'assignments/return_device_modal.html', context)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_statistics_view(request):
    """Get assignment statistics"""
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Calculate statistics
    total_assignments = Assignment.objects.count()
    active_assignments = Assignment.objects.filter(status='active').count()
    returned_this_month = Assignment.objects.filter(
        status='returned',
        actual_return_date__gte=current_month_start
    ).count()
    
    # Calculate overdue assignments (active assignments past their expected return date)
    overdue_assignments = Assignment.objects.filter(
        status='active',
        expected_return_date__lt=today
    ).count()
    
    return Response({
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'returned_this_month': returned_this_month,
        'overdue_assignments': overdue_assignments
    })


@permission_required_redirect('devices.can_assign_devices', message='You do not have permission to assign devices.')
def assign_device_view(request, device_id=None):
    """Assign device to employee view"""

    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                device_id = request.POST.get('device')
                employee_id = request.POST.get('employee')
                assignment_type = request.POST.get('assignment_type')
                usage_mode = request.POST.get('usage_mode', 'individual')
                purpose = request.POST.get('purpose', '')
                location = request.POST.get('location', '')
                notes = request.POST.get('notes', '')
                expected_return_date = request.POST.get('expected_return_date')

                if not device_id or not employee_id or not assignment_type:
                    return JsonResponse({'error': 'Please select a device, employee, and assignment type.'}, status=400)

                device = Device.objects.get(id=device_id)
                employee = Employee.objects.get(id=employee_id)

                # Check if device is available
                if device.status != 'available':
                    return JsonResponse({'error': f'Device {device.asset_tag} is not available for assignment.'}, status=400)

                # Update device usage type based on mode selection
                if usage_mode == 'shared':
                    device.usage_type = 'shared'

                # Check if user needs approval for device assignments
                if request.user.can_manage_system_settings:
                    # Admin users can directly assign devices
                    assignment = Assignment.objects.create(
                        device=device,
                        employee=employee,
                        assigned_by=request.user,
                        assigned_date=timezone.now(),
                        expected_return_date=expected_return_date if expected_return_date else None,
                        purpose=f"{assignment_type}: {purpose}".strip(': '),
                        location=location,
                        notes=notes,
                        status='active'
                    )

                    # Update device status
                    device.status = 'assigned'
                    device.assigned_to = employee
                    device.save()

                    # Create device history record
                    from devices.models import DeviceHistory
                    DeviceHistory.objects.create(
                        device=device,
                        action='assigned',
                        new_employee=employee,
                        new_status='assigned',
                        previous_status='available',
                        notes=f'Assigned via assignment form: {notes}',
                        created_by=request.user
                    )

                    # Return success and trigger modal close + page redirect
                    from django.http import HttpResponse
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'assignmentCreated'
                    # Use HX-Redirect to force full navigation and bypass cache
                    response['HX-Redirect'] = request.META.get('HTTP_REFERER', '/assignments/')
                    return response
                else:
                    # Staff users need approval for device assignments
                    from approvals.views import create_approval_request

                    # Build request data
                    request_data = {
                        'device_id': device.id,
                        'employee_id': employee.id,
                        'assignment_type': assignment_type,
                        'purpose': purpose,
                        'location': location,
                        'notes': notes,
                        'expected_return_date': expected_return_date,
                    }

                    # Create approval request
                    approval_request = create_approval_request(
                        request_type='device_assignment',
                        title=f'Device Assignment Request: {device.asset_tag}',
                        description=f'Request to assign device {device.asset_tag} to {employee.get_full_name()}. Purpose: {assignment_type}: {purpose}',
                        request_data=request_data,
                        requested_by=request.user,
                        devices=[device],
                        priority='medium'
                    )

                    # Return success with approval info
                    from django.http import HttpResponse
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'approvalCreated'
                    # Use HX-Redirect to force full navigation and bypass cache
                    response['HX-Redirect'] = request.META.get('HTTP_REFERER', '/assignments/')
                    return response

            except Device.DoesNotExist:
                return JsonResponse({'error': 'Selected device does not exist.'}, status=400)
            except Employee.DoesNotExist:
                return JsonResponse({'error': 'Selected employee does not exist.'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Error assigning device: {str(e)}'}, status=400)
        else:
            # Handle regular form submission
            try:
                device_id = request.POST.get('device')
                employee_id = request.POST.get('employee')
                assignment_type = request.POST.get('assignment_type')
                purpose = request.POST.get('purpose', '')
                location = request.POST.get('location', '')
                notes = request.POST.get('notes', '')
                expected_return_date = request.POST.get('expected_return_date')

                if not device_id or not employee_id or not assignment_type:
                    messages.error(request, 'Please select a device, employee, and assignment type.')
                    return redirect('assign-device')

                device = Device.objects.get(id=device_id)
                employee = Employee.objects.get(id=employee_id)

                # Check if device is available
                if device.status != 'available':
                    messages.error(request, f'Device {device.asset_tag} is not available for assignment.')
                    return redirect('assign-device')

                # Check if user needs approval for device assignments
                if request.user.can_manage_system_settings:
                    # Admin users can directly assign devices
                    assignment = Assignment.objects.create(
                        device=device,
                        employee=employee,
                        assigned_by=request.user,
                        assigned_date=timezone.now(),
                        expected_return_date=expected_return_date if expected_return_date else None,
                        condition_at_assignment=condition_at_assignment,
                        purpose=f"{assignment_type}: {purpose}".strip(': '),
                        location=location,
                        notes=notes,
                        status='active'
                    )

                    # Update device status
                    device.status = 'assigned'
                    device.assigned_to = employee
                    device.save()

                    messages.success(request, f'Device {device.asset_tag} successfully assigned to {employee.get_full_name()}.')
                    return redirect('assignment-detail-page', assignment_id=assignment.id)
                else:
                    # Staff users need approval for device assignments
                    from approvals.views import create_approval_request

                    # Build request data
                    request_data = {
                        'device_id': device.id,
                        'employee_id': employee.id,
                        'assignment_type': assignment_type,
                        'purpose': purpose,
                        'location': location,
                        'notes': notes,
                        'expected_return_date': expected_return_date,
                    }

                    # Create approval request
                    approval_request = create_approval_request(
                        request_type='device_assignment',
                        title=f'Device Assignment Request: {device.asset_tag}',
                        description=f'Request to assign device {device.asset_tag} to {employee.get_full_name()}. Purpose: {assignment_type}: {purpose}',
                        request_data=request_data,
                        requested_by=request.user,
                        devices=[device],
                        priority='medium'
                    )

                    messages.success(request, f'Device assignment request submitted for approval. Request ID: {approval_request.id}')
                    return redirect('approvals')

            except Device.DoesNotExist:
                messages.error(request, 'Selected device does not exist.')
            except Employee.DoesNotExist:
                messages.error(request, 'Selected employee does not exist.')
            except Exception as e:
                messages.error(request, f'Error assigning device: {str(e)}')

            return redirect('assign-device')
    
    # GET request - show form
    # Get available devices
    available_devices = Device.objects.filter(status='available').select_related('device_model__category').order_by('asset_tag')

    # Get all employees
    employees = Employee.objects.all().order_by('employee_id')

    # If device_id is provided, get the device for preselection
    preselected_device = None
    if device_id:
        try:
            preselected_device = Device.objects.get(id=device_id)
            # Verify device is available
            if preselected_device.status != 'available':
                preselected_device = None
        except Device.DoesNotExist:
            preselected_device = None

    context = {
        'available_devices': available_devices,
        'employees': employees,
        'preselected_device': preselected_device,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'assignments/assign_device_modal.html', context)
    else:
        messages.info(request, 'Please use the Assign Device button from the devices page.')
        return redirect('devices')


@permission_required_redirect('assignments.can_view_assignments', message='You do not have permission to return devices.')
def return_device_view_page(request):
    """Return device page view"""
    
    if request.method == 'POST':
        try:
            assignment_id = request.POST.get('assignment')
            return_notes = request.POST.get('return_notes', '')
            retire_device = request.POST.get('retire_device') == '1'

            if not assignment_id:
                messages.error(request, 'Please select an assignment.')
                return redirect('return-device-page')

            assignment = Assignment.objects.get(id=assignment_id)

            # Check if assignment is active
            if assignment.status != 'active':
                messages.error(request, 'This assignment is not active.')
                return redirect('return-device-page')

            # Check if user needs approval for device returns
            if request.user.can_manage_system_settings:
                # Admin users can directly return devices
                assignment.return_device(
                    returned_by=request.user,
                    notes=return_notes
                )

                # Update device status based on retire_device checkbox
                device = assignment.device
                if retire_device:
                    device.status = 'retired'
                    messages.success(request, f'Device {device.asset_tag} successfully returned and retired.')
                else:
                    device.status = 'available'
                    messages.success(request, f'Device {device.asset_tag} successfully returned from {assignment.employee.get_full_name()}.')
                device.save()

                return redirect('assignment-detail-page', assignment_id=assignment.id)
            else:
                # Staff users need approval for device returns
                from approvals.views import create_approval_request

                # Build request data
                request_data = {
                    'assignment_id': assignment.id,
                    'device_id': assignment.device.id,
                    'employee_id': assignment.employee.id,
                    'return_notes': return_notes,
                    'retire_device': retire_device
                }

                # Build description
                description = f'Request to return device {assignment.device.asset_tag} from {assignment.employee.get_full_name()}.'
                if retire_device:
                    description += ' Device will be retired.'
                if return_notes:
                    description += f' Notes: {return_notes}'

                # Create approval request
                approval_request = create_approval_request(
                    request_type='device_return',
                    title=f'Device Return Request: {assignment.device.asset_tag}',
                    description=description,
                    request_data=request_data,
                    requested_by=request.user,
                    devices=[assignment.device],
                    priority='medium'
                )

                messages.success(request, f'Device return request submitted for approval. Request ID: {approval_request.id}')
                return redirect('approvals')
            
        except Assignment.DoesNotExist:
            messages.error(request, 'Selected assignment does not exist.')
        except Exception as e:
            messages.error(request, f'Error returning device: {str(e)}')
        
        return redirect('return-device-page')
    
    # GET request - show form
    active_assignments = Assignment.objects.filter(status='active').select_related('device', 'employee').order_by('-assigned_date')
    overdue_count = Assignment.objects.filter(status='active', expected_return_date__lt=timezone.now().date()).count()

    context = {
        'active_assignments': active_assignments,
        'overdue_count': overdue_count,
    }

    # HTMX requests get the modal content (unified template)
    if request.headers.get('HX-Request'):
        return render(request, 'assignments/return_device_modal.html', context)
    else:
        # Non-HTMX requests redirect to assignments page
        messages.info(request, 'Please use the Return Device button from the assignment or device page.')
        return redirect('assignments')
