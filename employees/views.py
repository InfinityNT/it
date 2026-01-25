from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import tempfile
import os
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
    queryset = Employee.objects.select_related('system_user', 'department', 'job_title')

    # Apply filters if any
    search = request.GET.get('search')
    department = request.GET.get('department')
    has_filters = bool(search or department)

    if search:
        queryset = queryset.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(employee_id__icontains=search) |
            models.Q(email__icontains=search)
        )
    if department:
        queryset = queryset.filter(department__name__icontains=department)

    employees = queryset.all()

    # Check if database is empty
    total_employees = Employee.objects.count() if not employees.exists() else None

    context = {
        'employees': employees,
        'has_filters': has_filters,
        'is_empty_database': total_employees == 0 if total_employees is not None else False,
    }

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


# Excel Import Views
@permission_required_redirect('employees.can_modify_employees', message='You do not have permission to import employees.')
def import_employees_modal_view(request):
    """Return the import employees modal content"""
    context = {
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'job_titles': JobTitle.objects.filter(is_active=True).order_by('title'),
    }
    return render(request, 'components/forms/import_employees_modal.html', context)


@permission_required_redirect('employees.can_modify_employees', message='You do not have permission to download import templates.')
def download_employee_template_view(request):
    """Generate and return Excel template for employee import"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = "Employee Import"

    # Define columns with headers
    columns = [
        ('employee_id', 'Employee ID *', 15),
        ('first_name', 'First Name *', 15),
        ('last_name', 'Last Name *', 15),
        ('email', 'Email *', 25),
        ('department_code', 'Department Code', 15),
        ('job_title', 'Job Title', 20),
        ('position', 'Position', 20),
        ('hire_date', 'Hire Date * (YYYY-MM-DD)', 22),
        ('employment_status', 'Employment Status', 18),
        ('work_phone', 'Work Phone', 15),
        ('mobile_phone', 'Mobile Phone', 15),
        ('work_email', 'Work Email', 25),
        ('office_location', 'Office Location', 20),
        ('desk_number', 'Desk Number', 12),
        ('cost_center', 'Cost Center', 15),
        ('manager_employee_id', 'Manager Employee ID', 20),
    ]

    # Style headers
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col_idx, (field, header, width) in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Add data validation for employment_status (column I)
    status_validation = DataValidation(
        type="list",
        formula1='"active,inactive,terminated,on_leave"',
        allow_blank=True
    )
    status_validation.error = "Please select a valid status"
    status_validation.errorTitle = "Invalid Status"
    ws.add_data_validation(status_validation)
    status_validation.add('I2:I1000')

    # Add instructions sheet
    instructions = wb.create_sheet("Instructions")
    instructions_text = [
        "Employee Import Template Instructions",
        "",
        "Required Fields (marked with *):",
        "- Employee ID: Unique identifier for the employee",
        "- First Name: Employee's first name",
        "- Last Name: Employee's last name",
        "- Email: Unique email address",
        "- Hire Date: Format YYYY-MM-DD (e.g., 2024-01-15)",
        "",
        "Optional Fields:",
        "- Department Code: Must match existing department code in system",
        "- Job Title: Must match existing job title in system",
        "- Position: Free text position description",
        "- Employment Status: active, inactive, terminated, or on_leave (default: active)",
        "- Work Phone, Mobile Phone: Phone numbers",
        "- Work Email: Secondary work email if different from primary",
        "- Office Location: Office/building location",
        "- Desk Number: Desk/cubicle number",
        "- Cost Center: Cost center code",
        "- Manager Employee ID: Employee ID of the manager",
        "",
        "Notes:",
        "- First row contains headers - do not modify",
        "- Duplicate employee_id or email values will cause errors",
        "- Invalid department codes or job titles will be skipped (employee still created)",
    ]
    for idx, text in enumerate(instructions_text, 1):
        instructions.cell(row=idx, column=1, value=text)
    instructions.column_dimensions['A'].width = 80

    # Add reference sheet with departments and job titles
    ref_sheet = wb.create_sheet("Reference Data")
    ref_sheet.cell(row=1, column=1, value="Department Code").font = Font(bold=True)
    ref_sheet.cell(row=1, column=2, value="Department Name").font = Font(bold=True)
    ref_sheet.cell(row=1, column=4, value="Job Title").font = Font(bold=True)

    departments = Department.objects.filter(is_active=True).order_by('name')
    for idx, dept in enumerate(departments, 2):
        ref_sheet.cell(row=idx, column=1, value=dept.code)
        ref_sheet.cell(row=idx, column=2, value=dept.name)

    job_titles = JobTitle.objects.filter(is_active=True).order_by('title')
    for idx, title in enumerate(job_titles, 2):
        ref_sheet.cell(row=idx, column=4, value=title.title)

    ref_sheet.column_dimensions['A'].width = 20
    ref_sheet.column_dimensions['B'].width = 30
    ref_sheet.column_dimensions['D'].width = 30

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="employee_import_template.xlsx"'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_employees_view(request):
    """Process Excel file and import employees"""
    from openpyxl import load_workbook

    # Check permission
    if not request.user.has_perm('employees.can_modify_employees'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get uploaded file
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate file type
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        return Response({'error': 'Invalid file type. Please upload an Excel file (.xlsx)'},
                       status=status.HTTP_400_BAD_REQUEST)

    # Check file size (max 5MB)
    if excel_file.size > 5 * 1024 * 1024:
        return Response({'error': 'File too large. Maximum size is 5MB'},
                       status=status.HTTP_400_BAD_REQUEST)

    temp_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            for chunk in excel_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        # Load workbook
        wb = load_workbook(temp_path, read_only=True, data_only=True)
        ws = wb.active

        # Get headers from first row
        headers = [cell.value for cell in ws[1]]

        # Build header mapping (handle variations in header names)
        header_map = {}
        for idx, header in enumerate(headers):
            if header:
                normalized = header.lower().replace(' ', '_').replace('*', '').strip()
                # Remove common suffixes
                normalized = normalized.replace('_(yyyy-mm-dd)', '').replace('(yyyy-mm-dd)', '').strip()
                header_map[normalized] = idx

        # Validate required headers
        required_headers = ['employee_id', 'first_name', 'last_name', 'email', 'hire_date']
        missing_headers = [h for h in required_headers if h not in header_map]
        if missing_headers:
            wb.close()
            return Response({
                'error': f'Missing required columns: {", ".join(missing_headers)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cache lookups for performance
        department_cache = {d.code.lower(): d for d in Department.objects.filter(is_active=True)}
        job_title_cache = {j.title.lower(): j for j in JobTitle.objects.filter(is_active=True)}
        existing_employee_ids = set(Employee.objects.values_list('employee_id', flat=True))
        existing_emails = set(e.lower() for e in Employee.objects.values_list('email', flat=True))

        results = {
            'success': [],
            'errors': [],
        }

        # Process rows
        with transaction.atomic():
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                # Skip empty rows
                if not any(row):
                    continue

                row_data = {}
                for field, col_idx in header_map.items():
                    if col_idx < len(row):
                        row_data[field] = row[col_idx]

                # Validate required fields
                row_errors = []
                employee_id = str(row_data.get('employee_id', '') or '').strip()
                email = str(row_data.get('email', '') or '').strip().lower()
                first_name = str(row_data.get('first_name', '') or '').strip()
                last_name = str(row_data.get('last_name', '') or '').strip()
                hire_date_raw = row_data.get('hire_date')

                if not employee_id:
                    row_errors.append('Employee ID is required')
                elif employee_id in existing_employee_ids:
                    row_errors.append(f'Employee ID "{employee_id}" already exists')

                if not email:
                    row_errors.append('Email is required')
                elif email in existing_emails:
                    row_errors.append(f'Email "{email}" already exists')

                if not first_name:
                    row_errors.append('First name is required')
                if not last_name:
                    row_errors.append('Last name is required')

                # Parse hire date
                hire_date = None
                if hire_date_raw:
                    if isinstance(hire_date_raw, datetime):
                        hire_date = hire_date_raw.date()
                    else:
                        try:
                            hire_date = datetime.strptime(str(hire_date_raw), '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                hire_date = datetime.strptime(str(hire_date_raw), '%m/%d/%Y').date()
                            except ValueError:
                                row_errors.append(f'Invalid hire date format: {hire_date_raw}')
                else:
                    row_errors.append('Hire date is required')

                if row_errors:
                    results['errors'].append({
                        'row': row_idx,
                        'employee_id': employee_id or 'N/A',
                        'errors': row_errors
                    })
                    continue

                # Lookup department
                department = None
                dept_code = str(row_data.get('department_code', '') or '').strip().lower()
                if dept_code and dept_code in department_cache:
                    department = department_cache[dept_code]

                # Lookup job title
                job_title = None
                job_title_name = str(row_data.get('job_title', '') or '').strip().lower()
                if job_title_name and job_title_name in job_title_cache:
                    job_title = job_title_cache[job_title_name]

                # Validate employment status
                employment_status = str(row_data.get('employment_status', '') or '').strip().lower()
                valid_statuses = ['active', 'inactive', 'terminated', 'on_leave']
                if employment_status and employment_status not in valid_statuses:
                    employment_status = 'active'
                elif not employment_status:
                    employment_status = 'active'

                # Create employee
                try:
                    employee = Employee.objects.create(
                        employee_id=employee_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        department=department,
                        job_title=job_title,
                        position=str(row_data.get('position', '') or '').strip(),
                        hire_date=hire_date,
                        employment_status=employment_status,
                        work_phone=str(row_data.get('work_phone', '') or '').strip(),
                        mobile_phone=str(row_data.get('mobile_phone', '') or '').strip(),
                        work_email=str(row_data.get('work_email', '') or '').strip(),
                        office_location=str(row_data.get('office_location', '') or '').strip(),
                        desk_number=str(row_data.get('desk_number', '') or '').strip(),
                        cost_center=str(row_data.get('cost_center', '') or '').strip(),
                        manager_employee_id=str(row_data.get('manager_employee_id', '') or '').strip(),
                    )
                    results['success'].append({
                        'row': row_idx,
                        'employee_id': employee_id,
                        'name': f'{first_name} {last_name}'
                    })
                    # Update caches to prevent duplicates within batch
                    existing_employee_ids.add(employee_id)
                    existing_emails.add(email)
                except Exception as e:
                    results['errors'].append({
                        'row': row_idx,
                        'employee_id': employee_id,
                        'errors': [str(e)]
                    })

        wb.close()

    except Exception as e:
        return Response({'error': f'Error processing file: {str(e)}'},
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

    return Response({
        'message': f'Import completed: {len(results["success"])} employees imported',
        'success_count': len(results['success']),
        'error_count': len(results['errors']),
        'results': results
    })
