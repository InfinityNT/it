from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Assignment
from .serializers import AssignmentSerializer, AssignmentListSerializer
from devices.models import Device
from core.models import User


# API Views for HTML responses
@ensure_csrf_cookie
@login_required
def assignment_list_api_view(request):
    """Assignment list API that returns HTML"""
    queryset = Assignment.objects.all()
    
    # Apply filters
    status_filter = request.GET.get('status')
    user_filter = request.GET.get('user')
    device_filter = request.GET.get('device')
    search = request.GET.get('search')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if user_filter:
        queryset = queryset.filter(user__id=user_filter)
    if device_filter:
        queryset = queryset.filter(device__id=device_filter)
    if search:
        queryset = queryset.filter(
            models.Q(device__asset_tag__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search) |
            models.Q(user__email__icontains=search)
        )
    
    assignments = queryset.select_related('device', 'user', 'assigned_by').order_by('-assigned_date')
    context = {'assignments': assignments}
    
    # Use different template for user-specific assignments
    if user_filter:
        return render(request, 'assignments/user_assignment_list.html', context)
    else:
        return render(request, 'assignments/assignment_list.html', context)


# JSON API Views
class AssignmentListView(generics.ListAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        user_filter = self.request.query_params.get('user')
        device_filter = self.request.query_params.get('device')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if user_filter:
            queryset = queryset.filter(user__id=user_filter)
        if device_filter:
            queryset = queryset.filter(device__id=device_filter)
        if search:
            queryset = queryset.filter(
                models.Q(device__asset_tag__icontains=search) |
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__email__icontains=search)
            )
        
        return queryset.select_related('device', 'user', 'assigned_by').order_by('-assigned_date')


class AssignmentDetailView(generics.RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Frontend Views
@login_required
def assignments_view(request):
    """Assignments management view"""
    return render(request, 'assignments/assignments.html')


@login_required
def assignment_detail_view(request, assignment_id):
    """Assignment detail view"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    context = {'assignment': assignment}
    return render(request, 'assignments/assignment_detail.html', context)


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
        user=device.assigned_to,
        status='active'
    ).first()
    
    if not assignment:
        return Response({'error': 'No active assignment found for this device'}, status=400)
    
    # Get return data from request
    condition = request.data.get('condition', device.condition)
    notes = request.data.get('notes', '')
    
    # Return the device
    assignment.return_device(
        returned_by=request.user,
        condition=condition,
        notes=notes
    )
    
    return Response({
        'message': f'Device {device.asset_tag} returned successfully',
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
        user=device.assigned_to,
        status='active'
    ).first()
    
    context = {
        'device': device,
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
