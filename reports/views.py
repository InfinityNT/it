from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from datetime import datetime, timedelta
import csv
import json

from devices.models import Device, DeviceCategory
from assignments.models import Assignment
from employees.models import Employee
from .models import ReportGeneration


@login_required
@permission_required('core.can_view_reports', raise_exception=True)
def reports_view(request):
    """Reports dashboard page - full page view"""
    return render(request, 'reports/reports.html')


@login_required
@permission_required('core.can_view_reports', raise_exception=True)
def reports_component_view(request):
    """Reports component view for SPA loading via HTMX"""
    return render(request, 'reports/reports_content.html')


@login_required
@permission_required('core.can_view_reports', raise_exception=True)
def custom_report_form_view(request):
    """Custom report generation form"""
    return render(request, 'reports/custom_report_form.html')


@login_required
def custom_report_modal_view(request):
    """Custom report modal content for HTMX"""
    return render(request, 'reports/custom_report_modal_content.html')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_summary_view(request):
    """Summary statistics for reports dashboard"""
    if not request.user.has_perm('core.can_view_reports'):
        return Response({'error': 'Permission denied'}, status=403)
    
    from devices.models import Device
    from assignments.models import Assignment
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    total_devices = Device.objects.count()
    assigned_devices = Device.objects.filter(status='assigned').count()
    available_devices = Device.objects.filter(status='available').count()

    utilization_rate = (assigned_devices / total_devices * 100) if total_devices > 0 else 0

    from django.db.models import F

    thirty_days_ago = timezone.now() - timedelta(days=30)
    avg_assignment_duration = Assignment.objects.filter(
        actual_return_date__isnull=False,
        assigned_date__gte=thirty_days_ago
    ).aggregate(
        avg_duration=Avg(F('actual_return_date') - F('assigned_date'))
    )

    avg_duration_days = avg_assignment_duration['avg_duration']
    if avg_duration_days:
        avg_duration_str = f'{avg_duration_days.days} days'
    else:
        avg_duration_str = 'N/A'

    summary_data = {
        'utilization_rate': f'{utilization_rate:.1f}%',
        'avg_assignment_duration': avg_duration_str,
        'total_devices': total_devices,
        'assigned_devices': assigned_devices,
        'available_devices': available_devices
    }
    
    html = f"""
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body">
                    <div class="row g-0 align-items-center">
                        <div class="col me-2">
                            <div class="text-xs fw-bold text-primary text-uppercase mb-1">
                                Total Devices
                            </div>
                            <div class="h5 mb-0 fw-bold text-body">
                                {summary_data['total_devices']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-laptop fs-2 text-muted"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-success shadow h-100 py-2">
                <div class="card-body">
                    <div class="row g-0 align-items-center">
                        <div class="col me-2">
                            <div class="text-xs fw-bold text-success text-uppercase mb-1">
                                Utilization Rate
                            </div>
                            <div class="h5 mb-0 fw-bold text-body">
                                {summary_data['utilization_rate']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-percent fs-2 text-muted"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-info shadow h-100 py-2">
                <div class="card-body">
                    <div class="row g-0 align-items-center">
                        <div class="col me-2">
                            <div class="text-xs fw-bold text-info text-uppercase mb-1">
                                Avg Assignment Duration
                            </div>
                            <div class="h5 mb-0 fw-bold text-body">
                                {summary_data['avg_assignment_duration']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-clock fs-2 text-muted"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-warning shadow h-100 py-2">
                <div class="card-body">
                    <div class="row g-0 align-items-center">
                        <div class="col me-2">
                            <div class="text-xs fw-bold text-warning text-uppercase mb-1">
                                Available Devices
                            </div>
                            <div class="h5 mb-0 fw-bold text-body">
                                {summary_data['available_devices']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-check-circle fs-2 text-muted"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """
    
    return HttpResponse(html)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_charts_view(request):
    """Chart data for reports dashboard"""
    if not request.user.has_perm('core.can_view_reports'):
        return Response({'error': 'Permission denied'}, status=403)
    
    from devices.models import Device, DeviceCategory
    from assignments.models import Assignment
    from django.db.models import Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Device distribution by category
    category_data = DeviceCategory.objects.annotate(
        device_count=Count('devicemodel__device')
    ).filter(device_count__gt=0)
    
    device_distribution = {
        'labels': [cat.name for cat in category_data],
        'values': [cat.device_count for cat in category_data]
    }
    
    # Status overview
    status_data = Device.objects.values('status').annotate(count=Count('id'))
    status_overview = {
        'labels': [item['status'].title() for item in status_data],
        'values': [item['count'] for item in status_data]
    }
    
    # Assignment trends (last 12 months)
    months = []
    assignments_data = []
    returns_data = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_assignments = Assignment.objects.filter(
            assigned_date__gte=month_start.date(),
            assigned_date__lte=month_end.date()
        ).count()
        
        month_returns = Assignment.objects.filter(
            actual_return_date__gte=month_start.date(),
            actual_return_date__lte=month_end.date()
        ).count()
        
        months.insert(0, month_start.strftime('%b %Y'))
        assignments_data.insert(0, month_assignments)
        returns_data.insert(0, month_returns)
    
    assignment_trends = {
        'labels': months,
        'assignments': assignments_data,
        'returns': returns_data
    }
    
    return Response({
        'device_distribution': device_distribution,
        'status_overview': status_overview,
        'assignment_trends': assignment_trends
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_top_users_view(request):
    """Top device users data"""
    if not request.user.has_perm('core.can_view_reports'):
        return Response({'error': 'Permission denied'}, status=403)
    
    from employees.models import Employee
    from django.db.models import Count
    
    top_users = Employee.objects.annotate(
        device_count=Count('device_assignments', distinct=True)
    ).filter(device_count__gt=0).order_by('-device_count')[:10]
    
    users_data = []
    for employee in top_users:
        users_data.append({
            'name': employee.get_full_name(),
            'email': employee.email,
            'device_count': employee.device_count
        })
    
    return Response({'users': users_data})


@login_required
@permission_required('core.can_generate_reports', raise_exception=True)
def reports_generate_view(request, report_type):
    """Generate and download reports with format selection"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    
    from django.http import HttpResponse
    from datetime import datetime
    import csv
    import json
    
    # Get the format from query parameter, default to CSV
    output_format = request.GET.get('format', 'csv')
    
    # Create report generation record
    report_gen = ReportGeneration.objects.create(
        report_type=report_type,
        format=output_format,
        filters={},
        generated_by=request.user,
        status='processing'
    )
    
    try:
        # Build queryset based on report type
        if report_type == 'inventory':
            queryset = Device.objects.select_related('device_model__category', 'device_model')
        elif report_type == 'assignments':
            queryset = Assignment.objects.select_related('device', 'employee', 'assigned_by')
        else:
            # Generic fallback
            queryset = Device.objects.all()[:10]
        
        record_count = queryset.count()
        
        # Generate report in requested format
        if output_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            if report_type == 'inventory':
                writer.writerow(['Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model', 'Status', 'Location'])
                for device in queryset:
                    writer.writerow([
                        device.asset_tag,
                        device.serial_number,
                        device.device_model.category.name if device.device_model else '',
                        device.device_model.manufacturer if device.device_model else '',
                        device.device_model.model_name if device.device_model else '',
                        device.get_status_display(),
                        device.location
                    ])
            elif report_type == 'assignments':
                writer.writerow(['Device', 'Employee', 'Assigned Date', 'Return Date', 'Status', 'Assigned By'])
                for assignment in queryset:
                    writer.writerow([
                        assignment.device.asset_tag,
                        assignment.employee.get_full_name(),
                        assignment.assigned_date.strftime('%Y-%m-%d'),
                        assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else '',
                        assignment.get_status_display(),
                        assignment.assigned_by.get_full_name()
                    ])
            else:
                writer.writerow(['Report Type', 'Generated Date'])
                writer.writerow([report_type.title(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            
            report_gen.mark_completed(record_count=record_count)
            return response
            
        elif output_format == 'json':
            data = []
            if report_type == 'inventory':
                for device in queryset:
                    data.append({
                        'asset_tag': device.asset_tag,
                        'serial_number': device.serial_number,
                        'category': device.device_model.category.name if device.device_model else '',
                        'manufacturer': device.device_model.manufacturer if device.device_model else '',
                        'model': device.device_model.model_name if device.device_model else '',
                        'status': device.status,
                        'location': device.location
                    })
            elif report_type == 'assignments':
                for assignment in queryset:
                    data.append({
                        'device': assignment.device.asset_tag,
                        'employee': assignment.employee.get_full_name(),
                        'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d'),
                        'return_date': assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else None,
                        'status': assignment.status,
                        'assigned_by': assignment.assigned_by.get_full_name()
                    })
            else:
                data = [{'report_type': report_type, 'generated_date': datetime.now().isoformat()}]
                
            response = HttpResponse(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            
            report_gen.mark_completed(record_count=record_count)
            return response
            
        elif output_format == 'pdf':
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                from io import BytesIO
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    spaceAfter=30,
                    alignment=1  # Center alignment
                )
                title = Paragraph(f"{report_type.title()} Report", title_style)
                elements.append(title)
                elements.append(Spacer(1, 12))
                
                # Report info
                info_style = styles['Normal']
                info = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Record count: {record_count}", info_style)
                elements.append(info)
                elements.append(Spacer(1, 20))
                
                # Create table data
                if report_type == 'inventory':
                    headers = ['Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model', 'Status', 'Location']
                    data = [headers]
                    for device in queryset[:100]:  # Limit to first 100 for PDF
                        data.append([
                            device.asset_tag or '',
                            device.serial_number or '',
                            device.device_model.category.name if device.device_model else '',
                            device.device_model.manufacturer if device.device_model else '',
                            device.device_model.model_name if device.device_model else '',
                            device.get_status_display(),
                            device.location or ''
                        ])
                elif report_type == 'assignments':
                    headers = ['Device', 'Employee', 'Assigned Date', 'Return Date', 'Status']
                    data = [headers]
                    for assignment in queryset[:100]:  # Limit to first 100 for PDF
                        data.append([
                            assignment.device.asset_tag,
                            assignment.employee.get_full_name(),
                            assignment.assigned_date.strftime('%Y-%m-%d'),
                            assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else '',
                            assignment.get_status_display()
                        ])
                else:
                    headers = ['Report Type', 'Generated Date']
                    data = [headers, [report_type.title(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]
                
                # Create and style table
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
                doc.build(elements)
                
                buffer.seek(0)
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                
                report_gen.mark_completed(record_count=record_count)
                return response
                
            except ImportError:
                # Fallback to CSV if reportlab is not installed
                report_gen.mark_failed('PDF generation library not available')
                return HttpResponse('PDF generation not available. Please try CSV format.', status=400)
        
        else:
            report_gen.mark_failed(f'Unsupported format: {output_format}')
            return HttpResponse(f'Unsupported format: {output_format}', status=400)
    
    except Exception as e:
        report_gen.mark_failed(str(e))
        return HttpResponse(f'Report generation failed: {str(e)}', status=500)


@login_required
@permission_required('core.can_generate_reports', raise_exception=True)
def generate_custom_report_view(request):
    """Generate custom report based on form data"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'inventory')
        output_format = request.POST.get('output_format', 'csv')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        status_filter = request.POST.getlist('status_filter')
        category_filter = request.POST.getlist('category_filter')
        location_filter = request.POST.get('location_filter')
        is_preview = request.POST.get('preview') == 'true'
        
        # Create report generation record
        report_gen = ReportGeneration.objects.create(
            report_type=report_type,
            format=output_format,
            filters={
                'start_date': start_date,
                'end_date': end_date,
                'status_filter': status_filter,
                'category_filter': category_filter,
                'location_filter': location_filter,
            },
            generated_by=request.user,
            status='processing'
        )
        
        try:
            # Build queryset based on report type and filters
            if report_type == 'inventory':
                queryset = Device.objects.select_related('device_model__category', 'device_model')
                
                if status_filter:
                    queryset = queryset.filter(status__in=status_filter)
                if category_filter:
                    queryset = queryset.filter(device_model__category__id__in=category_filter)
                if location_filter:
                    queryset = queryset.filter(location__icontains=location_filter)
                if start_date:
                    queryset = queryset.filter(created_at__gte=start_date)
                if end_date:
                    queryset = queryset.filter(created_at__lte=end_date)
                    
            elif report_type == 'assignments':
                queryset = Assignment.objects.select_related('device', 'employee', 'assigned_by')
                
                if start_date:
                    queryset = queryset.filter(assigned_date__gte=start_date)
                if end_date:
                    queryset = queryset.filter(assigned_date__lte=end_date)
                if status_filter:
                    queryset = queryset.filter(device__status__in=status_filter)
                if category_filter:
                    queryset = queryset.filter(device__device_model__category__id__in=category_filter)
                    
            else:
                queryset = Device.objects.all()[:10]  # Default fallback
            
            record_count = queryset.count()
            
            if is_preview:
                # Return preview data
                preview_data = []
                for item in queryset[:10]:  # First 10 records for preview
                    if report_type == 'inventory':
                        preview_data.append({
                            'asset_tag': item.asset_tag,
                            'model': str(item.device_model) if item.device_model else '',
                            'status': item.get_status_display(),
                            'location': item.location or ''
                        })
                    elif report_type == 'assignments':
                        preview_data.append({
                            'device': item.device.asset_tag,
                            'employee': item.employee.get_full_name(),
                            'assigned_date': item.assigned_date.strftime('%Y-%m-%d'),
                            'status': item.get_status_display()
                        })
                
                return JsonResponse({
                    'success': True,
                    'report_type': report_type,
                    'record_count': record_count,
                    'date_range': f"{start_date or 'All'} to {end_date or 'All'}",
                    'preview_data': json.dumps(preview_data, indent=2)
                })
            
            # Generate actual report
            if output_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{report_type}_custom_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
                
                writer = csv.writer(response)
                
                if report_type == 'inventory':
                    writer.writerow(['Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model', 'Status', 'Location'])
                    for device in queryset:
                        writer.writerow([
                            device.asset_tag,
                            device.serial_number,
                            device.device_model.category.name if device.device_model else '',
                            device.device_model.manufacturer if device.device_model else '',
                            device.device_model.model_name if device.device_model else '',
                            device.get_status_display(),
                            device.location
                        ])
                        
                elif report_type == 'assignments':
                    writer.writerow(['Device', 'Employee', 'Assigned Date', 'Return Date', 'Status', 'Assigned By'])
                    for assignment in queryset:
                        writer.writerow([
                            assignment.device.asset_tag,
                            assignment.employee.get_full_name(),
                            assignment.assigned_date.strftime('%Y-%m-%d'),
                            assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else '',
                            assignment.get_status_display(),
                            assignment.assigned_by.get_full_name()
                        ])
                
                report_gen.mark_completed(record_count=record_count)
                return response
                
            elif output_format == 'json':
                data = []
                if report_type == 'inventory':
                    for device in queryset:
                        data.append({
                            'asset_tag': device.asset_tag,
                            'serial_number': device.serial_number,
                            'category': device.device_model.category.name if device.device_model else '',
                            'manufacturer': device.device_model.manufacturer if device.device_model else '',
                            'model': device.device_model.model_name if device.device_model else '',
                            'status': device.status,
                            'location': device.location
                        })
                        
                response = HttpResponse(
                    json.dumps(data, indent=2),
                    content_type='application/json'
                )
                response['Content-Disposition'] = f'attachment; filename="{report_type}_custom_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                
                report_gen.mark_completed(record_count=record_count)
                return response
                
            elif output_format == 'pdf':
                try:
                    from reportlab.lib.pagesizes import letter, A4
                    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib import colors
                    from reportlab.lib.units import inch
                    from io import BytesIO
                    
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()
                    
                    # Title
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=16,
                        spaceAfter=30,
                        alignment=1  # Center alignment
                    )
                    title = Paragraph(f"{report_type.title()} Report", title_style)
                    elements.append(title)
                    elements.append(Spacer(1, 12))
                    
                    # Report info
                    info_style = styles['Normal']
                    info = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Record count: {record_count}", info_style)
                    elements.append(info)
                    elements.append(Spacer(1, 20))
                    
                    # Create table data
                    if report_type == 'inventory':
                        headers = ['Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model', 'Status', 'Location']
                        data = [headers]
                        for device in queryset[:100]:  # Limit to first 100 for PDF
                            data.append([
                                device.asset_tag or '',
                                device.serial_number or '',
                                device.device_model.category.name if device.device_model else '',
                                device.device_model.manufacturer if device.device_model else '',
                                device.device_model.model_name if device.device_model else '',
                                device.get_status_display(),
                                device.location or ''
                            ])
                    elif report_type == 'assignments':
                        headers = ['Device', 'Employee', 'Assigned Date', 'Return Date', 'Status']
                        data = [headers]
                        for assignment in queryset[:100]:  # Limit to first 100 for PDF
                            data.append([
                                assignment.device.asset_tag,
                                assignment.employee.get_full_name(),
                                assignment.assigned_date.strftime('%Y-%m-%d'),
                                assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else '',
                                assignment.get_status_display()
                            ])
                    
                    # Create and style table
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    elements.append(table)
                    doc.build(elements)
                    
                    buffer.seek(0)
                    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{report_type}_custom_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                    
                    report_gen.mark_completed(record_count=record_count)
                    return response
                    
                except ImportError:
                    # Fallback to CSV if reportlab is not installed
                    messages.error(request, 'PDF generation not available. Please install reportlab package.')
                    return redirect('reports:custom-report-form')
            
        except Exception as e:
            report_gen.mark_failed(str(e))
            if is_preview:
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Report generation failed: {str(e)}')
            return redirect('custom-report-form')
    
    return redirect('custom-report-form')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_categories_api_view(request):
    """API endpoint to get device categories for form dropdowns"""
    categories = DeviceCategory.objects.all()
    data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    return Response(data)


# =============================================================================
# DYNAMIC CUSTOM REPORT BUILDER
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_schema_api_view(request):
    """Get report schema for dynamic report builder"""
    from .report_schema import get_schema_for_frontend
    schema = get_schema_for_frontend()
    return Response(schema)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def suggest_primary_source_view(request):
    """Suggest primary source for multi-source report"""
    from .report_schema import (
        suggest_primary_source,
        get_join_path,
        validate_source_combination,
        REPORT_SCHEMA
    )

    try:
        sources = request.data.get('sources', [])

        if not sources:
            return Response({
                'error': 'No sources provided'
            }, status=400)

        # Validate source combination
        is_valid, error_msg = validate_source_combination(sources)
        if not is_valid:
            return Response({
                'error': error_msg
            }, status=400)

        # Get suggested primary source
        suggested = suggest_primary_source(sources)

        # Build join path descriptions
        join_paths = {}
        for source in sources:
            if source != suggested:
                join_info = get_join_path(suggested, source)
                if join_info:
                    join_paths[source] = join_info['description']

        return Response({
            'suggested': suggested,
            'suggested_label': REPORT_SCHEMA[suggested]['label'],
            'join_paths': join_paths
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_dynamic_report_view(request):
    """Generate dynamic custom report based on user selections"""
    from .query_builder import DynamicReportBuilder
    from .formatters import ReportFormatter

    try:
        # Parse request data
        # Support both old single source and new multi-source format
        data_sources_json = request.POST.get('data_sources')
        if data_sources_json:
            # New multi-source format
            data_sources = json.loads(data_sources_json)
            primary_source = request.POST.get('primary_source')
        else:
            # Old single source format (backwards compatible)
            data_source = request.POST.get('data_source')
            data_sources = [data_source] if data_source else []
            primary_source = data_source

        fields_json = request.POST.get('fields', '[]')
        fields = json.loads(fields_json)
        is_preview = request.POST.get('preview') == 'true'
        output_format = request.POST.get('format', 'csv')

        # Build filters
        filters = {}
        if request.POST.get('start_date'):
            filters['start_date'] = request.POST.get('start_date')
        if request.POST.get('end_date'):
            filters['end_date'] = request.POST.get('end_date')
        if request.POST.getlist('status'):
            filters['status'] = request.POST.getlist('status')

        # Create report builder with multi-source support
        builder = DynamicReportBuilder(
            data_sources=data_sources,
            selected_fields=fields,
            filters=filters,
            primary_source=primary_source
        )

        # Build queryset
        queryset = builder.build_queryset()
        record_count = queryset.count()

        # Preview mode
        if is_preview:
            preview_data = []
            field_labels = builder.get_field_labels()

            for obj in queryset[:10]:
                values = builder.extract_values(obj)
                # Use labels as keys
                labeled_values = {
                    field_labels[key]: value
                    for key, value in values.items()
                }
                preview_data.append(labeled_values)

            return JsonResponse({
                'success': True,
                'record_count': record_count,
                'preview_data': preview_data
            })

        # Generate full report
        # Prepare data for formatter
        data_rows = []
        field_labels = builder.get_field_labels()

        for obj in queryset:
            values = builder.extract_values(obj)
            data_rows.append(values)

        # Generate filename with source info
        source_name = '_'.join(data_sources) if len(data_sources) > 1 else data_sources[0]
        timestamp = timezone.now().strftime("%Y%m%d")

        # Use the existing formatter
        if output_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="custom_report_{source_name}_{timestamp}.csv"'

            writer = csv.writer(response)
            # Write headers using labels
            writer.writerow([field_labels[f] for f in fields])
            # Write data
            for row in data_rows:
                writer.writerow([row[f] for f in fields])

            return response

        elif output_format == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="custom_report_{source_name}_{timestamp}.json"'

            # Convert to labeled format
            labeled_data = []
            for row in data_rows:
                labeled_row = {field_labels[key]: value for key, value in row.items()}
                labeled_data.append(labeled_row)

            response.write(json.dumps(labeled_data, indent=2))
            return response

        else:
            return JsonResponse({'success': False, 'error': 'Unsupported format'}, status=400)

    except Exception as e:
        import traceback
        traceback.print_exc()
        if is_preview:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        return JsonResponse({'error': str(e)}, status=500)
