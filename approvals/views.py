from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import models
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import ApprovalRequest, ApprovalRule, ApprovalComment
from core.models import User
from devices.models import Device


def check_approval_rules(request_data):
    """Check if a request matches any approval rules"""
    rules = ApprovalRule.objects.filter(is_active=True).order_by('order')
    
    for rule in rules:
        if rule.matches_request(request_data):
            return rule
    
    return None


def create_approval_request(request_type, title, description, request_data, requested_by, devices=None, priority='medium'):
    """Create a new approval request"""
    
    # Create the request object for rule checking
    temp_request = type('obj', (object,), {
        'request_type': request_type,
        'request_data': request_data,
        'requested_by': requested_by
    })
    
    # Check rules
    matching_rule = check_approval_rules(temp_request)
    
    # Create the approval request
    approval_request = ApprovalRequest.objects.create(
        request_type=request_type,
        title=title,
        description=description,
        request_data=request_data,
        requested_by=requested_by,
        priority=matching_rule.priority_override if matching_rule and matching_rule.priority_override else priority,
        assigned_to=matching_rule.assign_to if matching_rule else None,
        expires_at=timezone.now() + timedelta(days=7)  # Default 7 day expiry
    )
    
    # Add devices if provided
    if devices:
        approval_request.devices.set(devices)
    
    # Auto-approve if rule says so
    if matching_rule and matching_rule.auto_approve:
        approval_request.auto_approve()
    
    return approval_request


@login_required
def approvals_view(request):
    """Approvals dashboard page"""
    return render(request, 'approvals/approvals.html')


@login_required
def approval_list_api_view(request):
    """Approval list API that returns HTML"""
    queryset = ApprovalRequest.objects.select_related(
        'requested_by', 'assigned_to', 'approved_by'
    ).prefetch_related('devices')
    
    # Apply filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    request_type_filter = request.GET.get('request_type')
    assigned_to_me = request.GET.get('assigned_to_me')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
    if request_type_filter:
        queryset = queryset.filter(request_type=request_type_filter)
    if assigned_to_me and assigned_to_me.lower() == 'true':
        queryset = queryset.filter(assigned_to=request.user)
    
    # Default to showing pending requests first
    if not status_filter:
        queryset = queryset.filter(status='pending')
    
    approvals = queryset.order_by('-created_at')[:50]  # Limit for performance
    context = {'approvals': approvals}
    return render(request, 'approvals/approval_list.html', context)


@login_required
def approval_detail_view(request, approval_id):
    """Approval detail view"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check if user can view this approval
    if not (approval.requested_by == request.user or 
            approval.assigned_to == request.user or 
            request.user.role in ['admin', 'manager']):
        messages.error(request, 'You do not have permission to view this approval.')
        return redirect('approvals')
    
    context = {
        'approval': approval,
        'comments': approval.comments.select_related('user').order_by('created_at')
    }
    return render(request, 'approvals/approval_detail.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_request_view(request, approval_id):
    """Approve an approval request"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check permissions
    if not (approval.assigned_to == request.user or request.user.role in ['admin', 'manager']):
        return Response({'error': 'You do not have permission to approve this request'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    if approval.status != 'pending':
        return Response({'error': 'Request is not pending approval'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    notes = request.data.get('notes', '')
    
    try:
        approval.approve(approved_by=request.user, notes=notes)
        return Response({'message': 'Request approved successfully'})
    except Exception as e:
        return Response({'error': f'Failed to approve request: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_request_view(request, approval_id):
    """Reject an approval request"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check permissions
    if not (approval.assigned_to == request.user or request.user.role in ['admin', 'manager']):
        return Response({'error': 'You do not have permission to reject this request'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    if approval.status != 'pending':
        return Response({'error': 'Request is not pending approval'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    reason = request.data.get('reason', '')
    if not reason:
        return Response({'error': 'Rejection reason is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        approval.reject(rejected_by=request.user, reason=reason)
        return Response({'message': 'Request rejected successfully'})
    except Exception as e:
        return Response({'error': f'Failed to reject request: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_comment_view(request, approval_id):
    """Add a comment to an approval request"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check if user can comment
    if not (approval.requested_by == request.user or 
            approval.assigned_to == request.user or 
            request.user.role in ['admin', 'manager']):
        return Response({'error': 'You do not have permission to comment on this request'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    comment_text = request.data.get('comment', '').strip()
    if not comment_text:
        return Response({'error': 'Comment cannot be empty'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    comment = ApprovalComment.objects.create(
        request=approval,
        user=request.user,
        comment=comment_text
    )
    
    return Response({
        'message': 'Comment added successfully',
        'comment': {
            'id': comment.id,
            'user': request.user.get_full_name(),
            'comment': comment.comment,
            'created_at': comment.created_at.isoformat()
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_device_assignment_view(request):
    """Create an approval request for device assignment"""
    device_id = request.data.get('device_id')
    user_id = request.data.get('user_id')
    expected_return_date = request.data.get('expected_return_date')
    notes = request.data.get('notes', '')
    
    if not device_id or not user_id:
        return Response({'error': 'Device ID and User ID are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = Device.objects.get(id=device_id)
        user = User.objects.get(id=user_id)
    except (Device.DoesNotExist, User.DoesNotExist):
        return Response({'error': 'Device or User not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    if device.status != 'available':
        return Response({'error': 'Device is not available for assignment'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate assignment days for rule checking
    assignment_days = 30  # Default
    if expected_return_date:
        from datetime import datetime
        try:
            return_date = datetime.strptime(expected_return_date, '%Y-%m-%d').date()
            assignment_days = (return_date - timezone.now().date()).days
        except ValueError:
            pass
    
    # Create approval request
    request_data = {
        'device_id': device_id,
        'user_id': user_id,
        'expected_return_date': expected_return_date,
        'notes': notes,
        'device_value': float(device.purchase_price) if device.purchase_price else 0,
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
        priority='high' if request_data['device_value'] > 1000 else 'medium'
    )
    
    return Response({
        'message': 'Assignment request created successfully',
        'approval_request_id': approval_request.id,
        'status': approval_request.status
    })


@login_required
def approval_statistics_view(request):
    """Approval statistics API"""
    from django.db.models import Count, Q
    
    stats = {
        'pending_count': ApprovalRequest.objects.filter(status='pending').count(),
        'pending_high_priority': ApprovalRequest.objects.filter(
            status='pending', priority__in=['high', 'urgent']
        ).count(),
        'assigned_to_me': ApprovalRequest.objects.filter(
            assigned_to=request.user, status='pending'
        ).count(),
        'my_requests': ApprovalRequest.objects.filter(
            requested_by=request.user, status='pending'
        ).count(),
        'overdue_requests': ApprovalRequest.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        ).count()
    }
    
    context = {'stats': stats}
    return render(request, 'approvals/approval_stats.html', context)