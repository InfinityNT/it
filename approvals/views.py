from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import models, transaction
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta, datetime

from .models import ApprovalRequest, ApprovalComment
from core.models import User
from devices.models import Device


def create_approval_request(request_type, title, description, request_data, requested_by, devices=None, priority='medium'):
    """Create a new approval request - Group-based system"""
    
    # Only IT Staff can create approval requests
    if not requested_by.can_modify_assignments:
        raise PermissionError("Only IT Staff can create approval requests")
    
    # Get IT Manager to assign request to
    it_admin = User.objects.filter(is_active=True).filter(
        models.Q(is_superuser=True) | 
        models.Q(groups__permissions__codename='can_manage_system')
    ).first()
    if not it_admin:
        raise ValueError("No active IT Admin found to assign approval request")
    
    # Create the approval request - always assigned to IT Admin
    approval_request = ApprovalRequest.objects.create(
        request_type=request_type,
        title=title,
        description=description,
        request_data=request_data,
        requested_by=requested_by,
        assigned_to=it_admin,  # Always assign to IT Admin
        priority=priority,
        expires_at=timezone.now() + timedelta(days=7)  # Default 7 day expiry
    )
    
    # Add devices if provided
    if devices:
        approval_request.devices.set(devices)
    
    # No auto-approval in group-based system - everything needs IT Admin approval
    
    return approval_request


@login_required
def approvals_view(request):
    """Approvals dashboard page - Group-based access"""
    # Only users with assignment modification permissions can access approvals
    if not request.user.can_modify_assignments:
        messages.error(request, 'You do not have permission to access approvals.')
        return redirect('dashboard')

    return render(request, 'approvals/approvals.html')


@login_required
def approval_list_api_view(request):
    """Approval list API that returns HTML - Group-based filtering"""
    # Only users with assignment modification permissions can access approvals
    if not request.user.can_modify_assignments:
        return JsonResponse({'error': 'Access denied'}, status=403)

    queryset = ApprovalRequest.objects.select_related(
        'requested_by', 'assigned_to', 'approved_by'
    ).prefetch_related('devices')

    # Role-based filtering
    if request.user.can_modify_assignments and not request.user.can_manage_system_settings:
        # IT Staff can only see their own requests
        queryset = queryset.filter(requested_by=request.user)
    elif request.user.can_manage_system_settings:
        # IT Admin can see all requests (they're all assigned to them)
        queryset = queryset.filter(assigned_to=request.user)

    # Apply filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    request_type_filter = request.GET.get('request_type')

    # Track if user has applied explicit filters
    has_filters = bool(status_filter or priority_filter or request_type_filter)

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
    if request_type_filter:
        queryset = queryset.filter(request_type=request_type_filter)

    # Default to showing pending requests first
    if not status_filter:
        queryset = queryset.filter(status='pending')

    approvals = queryset.order_by('-created_at')[:50]  # Limit for performance

    # Check if database is empty
    total_approvals = ApprovalRequest.objects.count() if not approvals.exists() else None

    context = {
        'approvals': approvals,
        'user_role': 'IT_Managers' if request.user.can_manage_system_settings else ('IT_Staff' if request.user.can_modify_assignments else 'Viewers'),
        'has_filters': has_filters,
        'is_empty_database': total_approvals == 0 if total_approvals is not None else False,
    }
    return render(request, 'components/approvals/list.html', context)


@login_required
def approval_detail_view(request, approval_id):
    """Approval detail view - Group-based access"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check if user can view this approval - Group-based permissions
    can_view = False
    if request.user.can_modify_assignments and not request.user.can_manage_system_settings:
        # IT Staff can only view their own requests
        can_view = approval.requested_by == request.user
    elif request.user.can_manage_system_settings:
        # IT Admin can view all requests (they're all assigned to them)
        can_view = True
    
    if not can_view:
        messages.error(request, 'You do not have permission to view this approval.')
        return redirect('approvals')
    
    context = {
        'approval': approval,
        'comments': approval.comments.select_related('user').order_by('created_at'),
        'user_role': 'IT_Managers' if request.user.can_manage_system_settings else ('IT_Staff' if request.user.can_modify_assignments else 'Viewers')
    }
    return render(request, 'approvals/approval_detail.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_request_view(request, approval_id):
    """Approve an approval request - Only IT Admin can approve"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Only system managers can approve requests
    if not (request.user.can_manage_system_settings or request.user.is_superuser):
        return Response({'error': 'Only system managers can approve requests'}, 
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
    """Reject an approval request - Only IT Admin can reject"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Only system managers can reject requests
    if not (request.user.can_manage_system_settings or request.user.is_superuser):
        return Response({'error': 'Only system managers can reject requests'}, 
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
    """Add a comment to an approval request - Group-based access"""
    approval = get_object_or_404(ApprovalRequest, id=approval_id)
    
    # Check if user can comment - Group-based permissions
    can_comment = False
    if request.user.can_modify_assignments and not request.user.can_manage_system_settings:
        # IT Staff can only comment on their own requests
        can_comment = approval.requested_by == request.user
    elif request.user.can_manage_system_settings:
        # IT Admin can comment on all requests
        can_comment = True
    
    if not can_comment:
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
    """Create an approval request for device assignment - Only IT Staff can request"""
    # Only users with assignment modification permissions can create approval requests
    if not request.user.can_modify_assignments:
        return Response({'error': 'Only users with assignment permissions can create approval requests'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    device_id = request.data.get('device_id')
    employee_id = request.data.get('employee_id')
    expected_return_date = request.data.get('expected_return_date')
    notes = request.data.get('notes', '')
    
    if not device_id or not employee_id:
        return Response({'error': 'Device ID and Employee ID are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = Device.objects.get(id=device_id)
        from employees.models import Employee
        employee = Employee.objects.get(id=employee_id)
    except (Device.DoesNotExist, Employee.DoesNotExist):
        return Response({'error': 'Device or Employee not found'}, 
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
        'message': 'Assignment request created successfully',
        'approval_request_id': approval_request.id,
        'status': approval_request.status
    })


@login_required
def approval_statistics_view(request):
    """Approval statistics API - Group-based stats"""
    from django.db.models import Count, Q
    
    # Only users with assignment modification permissions can access stats
    if not request.user.can_modify_assignments:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.user.can_modify_assignments and not request.user.can_manage_system_settings:
        # IT Staff stats - only their own requests
        stats = {
            'pending_count': ApprovalRequest.objects.filter(
                requested_by=request.user, status='pending'
            ).count(),
            'pending_high_priority': ApprovalRequest.objects.filter(
                requested_by=request.user, status='pending', priority__in=['high', 'urgent']
            ).count(),
            'assigned_to_me': 0,  # Staff don't get assignments
            'my_requests': ApprovalRequest.objects.filter(
                requested_by=request.user, status='pending'
            ).count(),
            'overdue_requests': ApprovalRequest.objects.filter(
                requested_by=request.user, status='pending',
                expires_at__lt=timezone.now()
            ).count()
        }
    elif request.user.can_manage_system_settings:
        # IT Admin stats - all requests assigned to them
        stats = {
            'pending_count': ApprovalRequest.objects.filter(
                assigned_to=request.user, status='pending'
            ).count(),
            'pending_high_priority': ApprovalRequest.objects.filter(
                assigned_to=request.user, status='pending', priority__in=['high', 'urgent']
            ).count(),
            'assigned_to_me': ApprovalRequest.objects.filter(
                assigned_to=request.user, status='pending'
            ).count(),
            'my_requests': 0,  # Admin doesn't create requests
            'overdue_requests': ApprovalRequest.objects.filter(
                assigned_to=request.user, status='pending',
                expires_at__lt=timezone.now()
            ).count()
        }
    
    context = {
        'stats': stats,
        'user_role': 'IT_Managers' if request.user.can_manage_system_settings else ('IT_Staff' if request.user.can_modify_assignments else 'Viewers')
    }
    return render(request, 'components/approvals/stats.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approval_bulk_operations_view(request):
    """Bulk operations for approval requests"""
    approval_ids = request.data.get('item_ids', [])
    operation = request.data.get('operation')
    
    if not approval_ids or not operation:
        return Response({'error': 'Approval IDs and operation are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    approvals = ApprovalRequest.objects.filter(id__in=approval_ids)
    if not approvals.exists():
        return Response({'error': 'No valid approval requests found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Check base permissions
    if not request.user.can_modify_assignments:
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    updated_count = 0
    errors = []
    
    try:
        with transaction.atomic():
            if operation == 'bulk_approve':
                # Only system managers can approve
                if not request.user.can_manage_system_settings:
                    return Response({'error': 'Only system managers can approve requests'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                approval_notes = request.data.get('approval_notes', '')
                execute_immediately = request.data.get('execute_immediately', True)
                
                for approval in approvals:
                    if approval.status != 'pending':
                        errors.append(f'Request #{approval.id} is not pending approval')
                        continue
                    
                    try:
                        approval.approve(approved_by=request.user, notes=approval_notes)
                        updated_count += 1
                    except Exception as e:
                        errors.append(f'Failed to approve request #{approval.id}: {str(e)}')
            
            elif operation == 'bulk_reject':
                # Only system managers can reject
                if not request.user.can_manage_system_settings:
                    return Response({'error': 'Only system managers can reject requests'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                rejection_reason = request.data.get('rejection_reason')
                notify_requesters = request.data.get('notify_requesters', True)
                
                if not rejection_reason:
                    return Response({'error': 'Rejection reason is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for approval in approvals:
                    if approval.status != 'pending':
                        errors.append(f'Request #{approval.id} is not pending approval')
                        continue
                    
                    try:
                        approval.reject(rejected_by=request.user, reason=rejection_reason)
                        updated_count += 1
                    except Exception as e:
                        errors.append(f'Failed to reject request #{approval.id}: {str(e)}')
            
            elif operation == 'update_priority':
                # Only system managers can update priority
                if not request.user.can_manage_system_settings:
                    return Response({'error': 'Only system managers can update priority'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                new_priority = request.data.get('new_priority')
                priority_reason = request.data.get('priority_reason', '')
                
                if not new_priority:
                    return Response({'error': 'New priority is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for approval in approvals:
                    if approval.status != 'pending':
                        errors.append(f'Request #{approval.id} is not pending, cannot update priority')
                        continue
                    
                    old_priority = approval.priority
                    approval.priority = new_priority
                    
                    # Add priority change comment
                    comment_text = f'Priority changed from {old_priority} to {new_priority} by {request.user.get_full_name()}'
                    if priority_reason:
                        comment_text += f': {priority_reason}'
                    
                    ApprovalComment.objects.create(
                        request=approval,
                        user=request.user,
                        comment=comment_text
                    )
                    
                    approval.save()
                    updated_count += 1
            
            elif operation == 'reassign_approver':
                # Only system managers can reassign
                if not request.user.can_manage_system_settings:
                    return Response({'error': 'Only system managers can reassign approvers'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                new_approver_id = request.data.get('new_approver_id')
                reassignment_reason = request.data.get('reassignment_reason', '')
                notify_new_approver = request.data.get('notify_new_approver', True)
                
                if not new_approver_id:
                    return Response({'error': 'New approver is required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    new_approver = User.objects.get(id=new_approver_id)
                    if not new_approver.can_manage_system_settings:
                        return Response({'error': 'Selected user cannot approve requests'}, 
                                       status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({'error': 'New approver not found'}, 
                                   status=status.HTTP_404_NOT_FOUND)
                
                for approval in approvals:
                    if approval.status != 'pending':
                        errors.append(f'Request #{approval.id} is not pending, cannot reassign')
                        continue
                    
                    old_approver = approval.assigned_to
                    approval.assigned_to = new_approver
                    
                    # Add reassignment comment
                    comment_text = f'Reassigned from {old_approver.get_full_name() if old_approver else "unassigned"} to {new_approver.get_full_name()} by {request.user.get_full_name()}'
                    if reassignment_reason:
                        comment_text += f': {reassignment_reason}'
                    
                    ApprovalComment.objects.create(
                        request=approval,
                        user=request.user,
                        comment=comment_text
                    )
                    
                    approval.save()
                    updated_count += 1
            
            elif operation == 'extend_expiry':
                # Only system managers can extend expiry
                if not request.user.can_manage_system_settings:
                    return Response({'error': 'Only system managers can extend expiry'}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                extension_days = request.data.get('extension_days')
                extension_reason = request.data.get('extension_reason', '')
                
                if not extension_days or not isinstance(extension_days, int) or extension_days < 1 or extension_days > 30:
                    return Response({'error': 'Extension days must be between 1 and 30'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for approval in approvals:
                    if approval.status != 'pending':
                        errors.append(f'Request #{approval.id} is not pending, cannot extend expiry')
                        continue
                    
                    old_expiry = approval.expires_at
                    if approval.expires_at:
                        approval.expires_at = approval.expires_at + timedelta(days=extension_days)
                    else:
                        approval.expires_at = timezone.now() + timedelta(days=extension_days)
                    
                    # Add extension comment
                    comment_text = f'Expiry extended by {extension_days} days by {request.user.get_full_name()}'
                    if old_expiry:
                        comment_text += f' from {old_expiry.strftime("%Y-%m-%d %H:%M")} to {approval.expires_at.strftime("%Y-%m-%d %H:%M")}'
                    else:
                        comment_text += f' to {approval.expires_at.strftime("%Y-%m-%d %H:%M")}'
                    if extension_reason:
                        comment_text += f': {extension_reason}'
                    
                    ApprovalComment.objects.create(
                        request=approval,
                        user=request.user,
                        comment=comment_text
                    )
                    
                    approval.save()
                    updated_count += 1
            
            elif operation == 'add_comments':
                comment_category = request.data.get('comment_category')
                comment_text = request.data.get('comment_text')
                notify_requesters = request.data.get('notify_requesters', False)
                
                if not comment_category or not comment_text:
                    return Response({'error': 'Comment category and text are required'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                for approval in approvals:
                    # Check if user can comment on this request
                    can_comment = False
                    if request.user.can_manage_system_settings:
                        can_comment = True
                    elif request.user.can_modify_assignments and approval.requested_by == request.user:
                        can_comment = True
                    
                    if not can_comment:
                        errors.append(f'Cannot comment on request #{approval.id} - permission denied')
                        continue
                    
                    formatted_comment = f'[{comment_category.upper()}] {comment_text}'
                    
                    ApprovalComment.objects.create(
                        request=approval,
                        user=request.user,
                        comment=formatted_comment
                    )
                    updated_count += 1
            
            elif operation == 'export_selected':
                export_format = request.data.get('export_format', 'csv')
                include_comments = request.data.get('include_comments', True)
                include_device_details = request.data.get('include_device_details', True)
                
                # This would implement the export functionality
                # For now, just return success
                return Response({
                    'message': f'Export request created for {len(approval_ids)} approval requests',
                    'export_format': export_format,
                    'updated_count': len(approval_ids)
                })
            
            else:
                return Response({'error': 'Invalid operation'}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {
            'message': f'Successfully updated {updated_count} approval requests',
            'updated_count': updated_count,
            'total_requests': len(approval_ids)
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['error_count'] = len(errors)
        
        return Response(response_data)
    
    except Exception as e:
        return Response({'error': f'Bulk operation failed: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)