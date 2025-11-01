from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from .models import Employee, Department, JobTitle
from core.models import Location
from .serializers import EmployeeListSerializer, EmployeeSerializer
from core.models import User
from core.decorators import permission_required_redirect


@permission_required_redirect('employees.can_view_employees', message='You do not have permission to view employees.')
def employees_view(request):
    """Employee management view"""
    
    action = request.GET.get('action')
    if action == 'add':
        return redirect('add-employee')
    
    # Get all employees with related data
    employees = Employee.objects.select_related('system_user', 'department', 'job_title').all()
    
    context = {'employees': employees}

    # If HTMX request, return content fragment
    if request.headers.get('HX-Request'):
        return render(request, 'employees/employees_content.html', context)
    # If direct access, return full page
    else:
        return render(request, 'employees/employees.html', context)


@permission_required_redirect('employees.can_modify_employees', message='You do not have permission to add employees.')
def add_employee_view(request):
    """Add new employee view"""
    
    if request.method == 'POST':
        # Handle employee creation
        try:
            # Create employee record (independent of users)
            employee = Employee.objects.create(
                employee_id=request.POST.get('employee_id'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                department_id=request.POST.get('department') if request.POST.get('department') else None,
                job_title_id=request.POST.get('job_title') if request.POST.get('job_title') else None,
                hire_date=request.POST.get('hire_date'),
                work_phone=request.POST.get('work_phone', ''),
                mobile_phone=request.POST.get('mobile_phone', ''),
                work_email=request.POST.get('work_email', ''),
                office_location=request.POST.get('office_location', ''),
                desk_number=request.POST.get('desk_number', ''),
                cost_center=request.POST.get('cost_center', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                notes=request.POST.get('notes', ''),
                manager_employee_id=request.POST.get('manager_employee_id', '')
            )
            
            # Optionally create system user if requested
            create_system_user = request.POST.get('create_system_user') == 'on'
            if create_system_user:
                username = request.POST.get('username')
                password = request.POST.get('password', 'ChangeMe123!')
                group_id = request.POST.get('groups')
                
                if username:
                    user = User.objects.create_user(
                        username=username,
                        email=employee.email,
                        first_name=employee.first_name,
                        last_name=employee.last_name,
                        password=password
                    )
                    
                    # Assign to selected group
                    if group_id:
                        from django.contrib.auth.models import Group
                        try:
                            group = Group.objects.get(id=group_id)
                            user.groups.add(group)
                        except Group.DoesNotExist:
                            pass
                    employee.system_user = user
                    employee.save()
            
            messages.success(request, f'Employee {employee.get_full_name()} created successfully.')
            return redirect('employees')
            
        except Exception as e:
            messages.error(request, f'Error creating employee: {str(e)}')
    
    # Get departments, job titles, and groups for form dropdowns
    departments = Department.objects.filter(is_active=True).order_by('name')
    job_titles = JobTitle.objects.filter(is_active=True).order_by('title')
    
    # Get groups that current user can assign
    from django.contrib.auth.models import Group
    available_groups = []
    if request.user.has_perm('employees.can_modify_employees'):
        if request.user.can_manage_system_settings:
            # System managers can assign any group
            available_groups = Group.objects.all().order_by('name')
        else:
            # Regular users can only assign non-system management groups
            available_groups = Group.objects.exclude(permissions__codename='can_manage_system').order_by('name')
    
    context = {
        'departments': departments,
        'job_titles': job_titles,
        'locations': Location.objects.filter(is_active=True).order_by('name'),
        'available_groups': available_groups,
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'employees/add_employee_modal.html', context)
    # If direct access, return full page
    else:
        return render(request, 'employees/add_employee.html', context)


@login_required
@permission_required('employees.can_view_employees', raise_exception=True)
def employee_detail_view(request, employee_id):
    """Employee detail view"""

    employee = get_object_or_404(Employee, id=employee_id)

    context = {'employee': employee}

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'employees/employee_detail_modal.html', context)
    else:
        messages.info(request, 'Please use the employee list to view employee details.')
        return redirect('employees')


@login_required
@permission_required('employees.can_modify_employees', raise_exception=True)
def employee_edit_view(request, employee_id):
    """Employee edit view"""
    
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        try:
            # Update employee information
            employee.employee_id = request.POST.get('employee_id')
            employee.first_name = request.POST.get('first_name')
            employee.last_name = request.POST.get('last_name')
            employee.email = request.POST.get('email')
            employee.department_id = request.POST.get('department') if request.POST.get('department') else None
            employee.job_title_id = request.POST.get('job_title') if request.POST.get('job_title') else None
            employee.hire_date = request.POST.get('hire_date')
            employee.work_phone = request.POST.get('work_phone', '')
            employee.mobile_phone = request.POST.get('mobile_phone', '')
            employee.work_email = request.POST.get('work_email', '')
            employee.office_location = request.POST.get('office_location', '')
            employee.desk_number = request.POST.get('desk_number', '')
            employee.cost_center = request.POST.get('cost_center', '')
            employee.emergency_contact_name = request.POST.get('emergency_contact_name', '')
            employee.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
            employee.notes = request.POST.get('notes', '')
            employee.employment_status = request.POST.get('employment_status', 'active')
            employee.manager_employee_id = request.POST.get('manager_employee_id', '')
            employee.save()
            
            # Update linked system user if exists
            if employee.system_user:
                employee.system_user.first_name = employee.first_name
                employee.system_user.last_name = employee.last_name
                employee.system_user.email = employee.email
                employee.system_user.save()
            
            messages.success(request, f'Employee {employee.get_full_name()} updated successfully.')
            return redirect('employee-detail', employee_id=employee.id)
            
        except Exception as e:
            messages.error(request, f'Error updating employee: {str(e)}')
    
    # Get departments and job titles for form dropdowns
    departments = Department.objects.filter(is_active=True).order_by('name')
    job_titles = JobTitle.objects.filter(is_active=True).order_by('title')
    
    context = {
        'employee': employee,
        'departments': departments,
        'job_titles': job_titles,
        'locations': Location.objects.filter(is_active=True).order_by('name'),
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'employees/employee_edit_modal.html', context)
    else:
        messages.info(request, 'Please use the Edit button from the employee list.')
        return redirect('employees')


# API Views
class EmployeeListAPIView(generics.ListAPIView):
    """API view to list employees for dropdowns and filters"""
    queryset = Employee.objects.filter(employment_status='active')
    serializer_class = EmployeeListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        department = self.request.query_params.get('department')
        
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(employee_id__icontains=search)
            )
        
        if department:
            queryset = queryset.filter(department_id=department)
        
        return queryset.select_related('department', 'job_title').order_by('first_name', 'last_name')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def department_list_api(request):
    """API endpoint for getting departments for bulk operations"""
    departments = Department.objects.all().order_by('name')
    data = [{'id': dept.id, 'name': dept.name} for dept in departments]
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def job_title_list_api(request):
    """API endpoint for getting job titles for bulk operations"""
    job_titles = JobTitle.objects.all().order_by('title')
    data = [{'id': title.id, 'title': title.title} for title in job_titles]
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def employee_bulk_operations_view(request):
    """Bulk operations for employees"""
    employee_ids = request.data.get('item_ids', [])
    operation = request.data.get('operation')
    
    if not employee_ids or not operation:
        return Response({'error': 'Employee IDs and operation are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    employees = Employee.objects.filter(id__in=employee_ids)
    if not employees.exists():
        return Response({'error': 'No valid employees found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not request.user.has_perm('employees.can_modify_employees'):
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    updated_count = 0
    errors = []
    
    try:
        with transaction.atomic():
            if operation == 'update_status':
                new_status = request.data.get('new_employment_status')
                status_reason = request.data.get('status_reason', '')
                
                if not new_status:
                    return Response({'error': 'New employment status is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                # Check for sensitive operations
                if new_status == 'terminated' and not request.user.has_perm('core.can_manage_system'):
                    return Response({'error': 'Permission denied for termination operations'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                for employee in employees:
                    old_status = employee.employment_status
                    employee.employment_status = new_status
                    
                    # Add status change note
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] Status changed from {old_status} to {new_status} by {request.user.get_full_name()}'
                    if status_reason:
                        note += f': {status_reason}'
                    
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            elif operation == 'bulk_department_transfer':
                new_department_id = request.data.get('new_department_id')
                new_job_title_id = request.data.get('new_job_title_id')
                transfer_date = request.data.get('transfer_date')
                transfer_reason = request.data.get('transfer_reason', '')
                
                if not new_department_id:
                    return Response({'error': 'New department is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    new_department = Department.objects.get(id=new_department_id)
                except Department.DoesNotExist:
                    return Response({'error': 'Department not found'}, 
                                   status=status.HTTP_404_NOT_FOUND)
                
                new_job_title = None
                if new_job_title_id:
                    try:
                        new_job_title = JobTitle.objects.get(id=new_job_title_id)
                    except JobTitle.DoesNotExist:
                        errors.append('Job title not found, keeping existing titles')
                
                for employee in employees:
                    old_department = employee.department
                    old_job_title = employee.job_title
                    
                    employee.department = new_department
                    if new_job_title:
                        employee.job_title = new_job_title
                    
                    # Add transfer note
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] Department transfer from {old_department} to {new_department} by {request.user.get_full_name()}'
                    if new_job_title and old_job_title != new_job_title:
                        note += f', Job title changed from {old_job_title} to {new_job_title}'
                    if transfer_reason:
                        note += f': {transfer_reason}'
                    
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            elif operation == 'update_location':
                new_office_location = request.data.get('new_office_location')
                new_building = request.data.get('new_building', '')
                new_floor = request.data.get('new_floor', '')
                new_desk_number = request.data.get('new_desk_number', '')
                
                if not new_office_location:
                    return Response({'error': 'New office location is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for employee in employees:
                    old_location = employee.office_location
                    employee.office_location = new_office_location
                    
                    if new_building:
                        employee.building = new_building
                    if new_floor:
                        employee.floor = new_floor
                    if new_desk_number:
                        employee.desk_number = new_desk_number
                    
                    # Add location update note
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] Location updated from {old_location} to {new_office_location} by {request.user.get_full_name()}'
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            elif operation == 'update_contact_info':
                new_work_phone = request.data.get('new_work_phone')
                new_mobile_phone = request.data.get('new_mobile_phone')
                new_work_email = request.data.get('new_work_email')
                contact_update_reason = request.data.get('contact_update_reason', '')
                
                if not any([new_work_phone, new_mobile_phone, new_work_email]):
                    return Response({'error': 'At least one contact field is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for employee in employees:
                    updates = []
                    
                    if new_work_phone:
                        old_work_phone = employee.work_phone
                        employee.work_phone = new_work_phone
                        updates.append(f'work phone from {old_work_phone} to {new_work_phone}')
                    
                    if new_mobile_phone:
                        old_mobile_phone = employee.mobile_phone
                        employee.mobile_phone = new_mobile_phone
                        updates.append(f'mobile phone from {old_mobile_phone} to {new_mobile_phone}')
                    
                    if new_work_email:
                        old_work_email = employee.work_email
                        employee.work_email = new_work_email
                        updates.append(f'work email from {old_work_email} to {new_work_email}')
                    
                    if updates:
                        note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] Contact info updated ({", ".join(updates)}) by {request.user.get_full_name()}'
                        if contact_update_reason:
                            note += f': {contact_update_reason}'
                        
                        employee.notes = (employee.notes or '') + '\\n' + note
                        employee.save()
                        updated_count += 1
            
            elif operation == 'assign_manager':
                new_manager_id = request.data.get('new_manager_id')
                manager_assignment_date = request.data.get('manager_assignment_date')
                manager_assignment_notes = request.data.get('manager_assignment_notes', '')
                
                if not new_manager_id:
                    return Response({'error': 'Manager is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    new_manager = Employee.objects.get(id=new_manager_id)
                except Employee.DoesNotExist:
                    return Response({'error': 'Manager not found'}, 
                                   status=status.HTTP_404_NOT_FOUND)
                
                for employee in employees:
                    if employee.id == new_manager.id:
                        errors.append(f'Cannot assign {employee.get_full_name()} as their own manager')
                        continue
                    
                    old_manager = employee.manager_employee_id
                    employee.manager_employee_id = new_manager.employee_id
                    
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] Manager assigned: {new_manager.get_full_name()} by {request.user.get_full_name()}'
                    if manager_assignment_notes:
                        note += f': {manager_assignment_notes}'
                    
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            elif operation == 'update_access_level':
                system_access_action = request.data.get('system_access_action')
                user_groups = request.data.get('user_groups')
                access_reason = request.data.get('access_reason')
                
                if not system_access_action or not access_reason:
                    return Response({'error': 'Access action and reason are required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                # This operation requires system management permissions
                if not request.user.has_perm('core.can_manage_system'):
                    return Response({'error': 'Permission denied for access level changes'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                for employee in employees:
                    if system_access_action == 'grant':
                        # Create system user if doesn't exist
                        if not employee.system_user:
                            # This would need to be implemented based on your user creation logic
                            errors.append(f'System user creation for {employee.get_full_name()} needs manual setup')
                            continue
                    
                    elif system_access_action == 'revoke':
                        if employee.system_user:
                            employee.system_user.is_active = False
                            employee.system_user.save()
                    
                    # Add access change note
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] System access {system_access_action} by {request.user.get_full_name()}: {access_reason}'
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            elif operation == 'add_notes':
                note_category = request.data.get('note_category')
                note_content = request.data.get('note_content')
                
                if not note_category or not note_content:
                    return Response({'error': 'Note category and content are required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for employee in employees:
                    note = f'[{timezone.now().strftime("%Y-%m-%d %H:%M")}] {note_category.upper()} NOTE by {request.user.get_full_name()}: {note_content}'
                    employee.notes = (employee.notes or '') + '\\n' + note
                    employee.save()
                    updated_count += 1
            
            else:
                return Response({'error': 'Invalid operation'}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {
            'message': f'Successfully updated {updated_count} employees',
            'updated_count': updated_count,
            'total_employees': len(employee_ids)
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['error_count'] = len(errors)
        
        return Response(response_data)
    
    except Exception as e:
        return Response({'error': f'Bulk operation failed: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
