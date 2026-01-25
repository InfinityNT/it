"""
Report Schema - Defines available data sources and fields for dynamic reports
"""

# Define relationships between data sources for multi-source reports
RELATIONSHIPS = {
    'device_to_employee': {
        'via': 'reverse FK',
        'path': 'assignments__employee',
        'description': 'Device assigned to Employee via Assignment'
    },
    'device_to_assignment': {
        'via': 'reverse FK',
        'path': 'assignments',
        'description': 'Device to Assignments'
    },
    'device_to_approval': {
        'via': 'M2M',
        'path': 'approval_requests',
        'description': 'Device related to Approval Requests'
    },
    'employee_to_device': {
        'via': 'reverse FK',
        'path': 'device_assignments__device',
        'description': 'Employee assigned Devices via Assignment'
    },
    'employee_to_assignment': {
        'via': 'reverse FK',
        'path': 'device_assignments',
        'description': 'Employee to Assignments'
    },
    'assignment_to_device': {
        'via': 'forward FK',
        'path': 'device',
        'description': 'Assignment to Device'
    },
    'assignment_to_employee': {
        'via': 'forward FK',
        'path': 'employee',
        'description': 'Assignment to Employee'
    },
    'approval_to_device': {
        'via': 'M2M',
        'path': 'devices',
        'description': 'Approval Request to Devices'
    }
}

# Define available report data sources and their fields
REPORT_SCHEMA = {
    'device': {
        'label': 'Devices',
        'model': 'devices.Device',
        'icon': 'bi-laptop',
        'fields': {
            'asset_tag': {'label': 'Asset Tag', 'type': 'text'},
            'serial_number': {'label': 'Serial Number', 'type': 'text'},
            'device_model__name': {'label': 'Model', 'type': 'text'},
            'device_model__category__name': {'label': 'Category', 'type': 'text'},
            'status': {'label': 'Status', 'type': 'choice'},
            'condition': {'label': 'Condition', 'type': 'choice'},
            'purchase_date': {'label': 'Purchase Date', 'type': 'date'},
            'purchase_price': {'label': 'Purchase Price', 'type': 'number'},
            'warranty_expiry': {'label': 'Warranty Expiry', 'type': 'date'},
            'assigned_to__first_name': {'label': 'Assigned To (First)', 'type': 'text'},
            'assigned_to__last_name': {'label': 'Assigned To (Last)', 'type': 'text'},
            'location__name': {'label': 'Location', 'type': 'text'},
            'notes': {'label': 'Notes', 'type': 'text'},
            'created_at': {'label': 'Created Date', 'type': 'datetime'},
        }
    },
    'employee': {
        'label': 'Employees',
        'model': 'employees.Employee',
        'icon': 'bi-people',
        'fields': {
            'employee_id': {'label': 'Employee ID', 'type': 'text'},
            'first_name': {'label': 'First Name', 'type': 'text'},
            'last_name': {'label': 'Last Name', 'type': 'text'},
            'email': {'label': 'Email', 'type': 'text'},
            'phone': {'label': 'Phone', 'type': 'text'},
            'department__name': {'label': 'Department', 'type': 'text'},
            'job_title__title': {'label': 'Job Title', 'type': 'text'},
            'employment_status': {'label': 'Employment Status', 'type': 'choice'},
            'hire_date': {'label': 'Hire Date', 'type': 'date'},
            'termination_date': {'label': 'Termination Date', 'type': 'date'},
        }
    },
    'assignment': {
        'label': 'Assignments',
        'model': 'assignments.Assignment',
        'icon': 'bi-arrow-left-right',
        'fields': {
            'device__asset_tag': {'label': 'Device Asset Tag', 'type': 'text'},
            'device__device_model__name': {'label': 'Device Model', 'type': 'text'},
            'employee__first_name': {'label': 'Employee First Name', 'type': 'text'},
            'employee__last_name': {'label': 'Employee Last Name', 'type': 'text'},
            'employee__employee_id': {'label': 'Employee ID', 'type': 'text'},
            'assigned_date': {'label': 'Assignment Date', 'type': 'date'},
            'expected_return_date': {'label': 'Expected Return', 'type': 'date'},
            'actual_return_date': {'label': 'Actual Return', 'type': 'date'},
            'status': {'label': 'Status', 'type': 'choice'},
            'assigned_by__first_name': {'label': 'Assigned By (First)', 'type': 'text'},
            'assigned_by__last_name': {'label': 'Assigned By (Last)', 'type': 'text'},
            'notes': {'label': 'Notes', 'type': 'text'},
        }
    },
    'approval': {
        'label': 'Approvals',
        'model': 'approvals.ApprovalRequest',
        'icon': 'bi-check-circle',
        'fields': {
            'title': {'label': 'Title', 'type': 'text'},
            'request_type': {'label': 'Request Type', 'type': 'choice'},
            'status': {'label': 'Status', 'type': 'choice'},
            'priority': {'label': 'Priority', 'type': 'choice'},
            'requested_by__first_name': {'label': 'Requested By (First)', 'type': 'text'},
            'requested_by__last_name': {'label': 'Requested By (Last)', 'type': 'text'},
            'assigned_to__first_name': {'label': 'Assigned To (First)', 'type': 'text'},
            'assigned_to__last_name': {'label': 'Assigned To (Last)', 'type': 'text'},
            'created_at': {'label': 'Created Date', 'type': 'datetime'},
            'reviewed_at': {'label': 'Reviewed Date', 'type': 'datetime'},
        }
    }
}


def get_schema_for_frontend():
    """Return simplified schema for frontend consumption"""
    return {
        source: {
            'label': config['label'],
            'icon': config['icon'],
            'fields': [
                {
                    'key': field_key,
                    'label': field_config['label'],
                    'type': field_config['type']
                }
                for field_key, field_config in config['fields'].items()
            ]
        }
        for source, config in REPORT_SCHEMA.items()
    }


def get_model_for_source(source):
    """Get Django model path for a data source"""
    return REPORT_SCHEMA.get(source, {}).get('model')


def get_fields_for_source(source):
    """Get fields configuration for a data source"""
    return REPORT_SCHEMA.get(source, {}).get('fields', {})


def suggest_primary_source(sources):
    """
    Suggest which source should be primary based on selection
    Priority: device > employee > assignment > approval
    """
    if not sources:
        return None

    priority = ['device', 'employee', 'assignment', 'approval']
    for p in priority:
        if p in sources:
            return p

    # If none of the known sources, return first
    return sources[0]


def get_join_path(primary, secondary):
    """Get the join path from primary to secondary source"""
    key = f"{primary}_to_{secondary}"
    return RELATIONSHIPS.get(key)


def validate_source_combination(sources):
    """
    Validate that the selected sources can be joined
    Returns (is_valid, error_message)
    """
    if not sources or len(sources) == 1:
        return True, None

    primary = suggest_primary_source(sources)

    # Check that all secondary sources can join to primary
    for source in sources:
        if source != primary:
            join_info = get_join_path(primary, source)
            if not join_info:
                return False, f"Cannot join {primary} to {source}"

    return True, None
