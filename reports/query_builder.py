"""
Dynamic Query Builder - Builds Django querysets based on user selections
Supports multi-source reports with smart join detection
"""
from django.apps import apps
from .report_schema import (
    get_model_for_source,
    get_fields_for_source,
    get_join_path,
    suggest_primary_source,
    REPORT_SCHEMA
)


class DynamicReportBuilder:
    """Build dynamic Django querysets for custom reports with multi-source support"""

    def __init__(self, data_sources, selected_fields, filters=None, primary_source=None):
        """
        Initialize the query builder

        Args:
            data_sources: List of data sources (e.g., ['device', 'employee'])
            selected_fields: List of field keys to include in report (format: 'source__field')
            filters: Dict of filter criteria
            primary_source: Override for primary source (auto-detected if None)
        """
        # Handle both single source (string) and multi-source (list) for backwards compatibility
        if isinstance(data_sources, str):
            self.data_sources = [data_sources]
        else:
            self.data_sources = data_sources

        self.primary_source = primary_source or suggest_primary_source(self.data_sources)
        self.selected_fields = selected_fields
        self.filters = filters or {}

    def build_queryset(self):
        """Build and return the Django queryset with multi-source joins"""
        # Get the primary model
        model_path = get_model_for_source(self.primary_source)
        if not model_path:
            raise ValueError(f"Unknown data source: {self.primary_source}")

        app_label, model_name = model_path.split('.')
        model = apps.get_model(app_label, model_name)

        # Start with base queryset
        queryset = model.objects.all()

        # Apply joins for secondary sources
        select_related_fields = set()
        prefetch_related_fields = set()

        for source in self.data_sources:
            if source != self.primary_source:
                join_info = get_join_path(self.primary_source, source)
                if join_info:
                    path = join_info['path']
                    # M2M and reverse FK use prefetch_related
                    if join_info['via'] in ['M2M', 'reverse FK']:
                        prefetch_related_fields.add(path)
                    else:
                        # Forward FK uses select_related
                        select_related_fields.add(path)

        # Add select_related for nested fields within selected fields
        additional_select = self._get_select_related_fields()
        select_related_fields.update(additional_select)

        # Apply optimizations
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)

        # Apply filters
        queryset = self._apply_filters(queryset)

        return queryset

    def _get_select_related_fields(self):
        """Extract fields that need select_related optimization"""
        related_fields = set()

        for field in self.selected_fields:
            # Remove source prefix if present (format: source__field1__field2)
            field_path = field
            if '__' in field:
                # Check if first part is a data source
                parts = field.split('__')
                if parts[0] in self.data_sources:
                    # Skip the source prefix, use rest for relations
                    field_path = '__'.join(parts[1:])
                else:
                    field_path = field

            # If field_path contains '__', it's a related field
            if '__' in field_path:
                # Extract the relation path (everything before the last __)
                parts = field_path.split('__')
                # Add progressively deeper relations
                for i in range(1, len(parts)):
                    related_fields.add('__'.join(parts[:i]))

        return list(related_fields)

    def _apply_filters(self, queryset):
        """Apply filters to the queryset based on primary source"""
        filters = self.filters

        # Date range filters
        if filters.get('start_date'):
            # Use created_at or assigned_date depending on primary model
            date_field = 'assigned_date' if self.primary_source == 'assignment' else 'created_at'
            queryset = queryset.filter(**{f'{date_field}__gte': filters['start_date']})

        if filters.get('end_date'):
            date_field = 'assigned_date' if self.primary_source == 'assignment' else 'created_at'
            queryset = queryset.filter(**{f'{date_field}__lte': filters['end_date']})

        # Status filters
        if filters.get('status'):
            queryset = queryset.filter(status__in=filters['status'])

        # Category filters (for devices)
        if filters.get('category') and self.primary_source == 'device':
            queryset = queryset.filter(device_model__category__id__in=filters['category'])

        # Department filters (for employees)
        if filters.get('department'):
            if self.primary_source == 'employee':
                queryset = queryset.filter(department__id__in=filters['department'])
            elif self.primary_source == 'assignment':
                queryset = queryset.filter(employee__department__id__in=filters['department'])

        return queryset

    def get_field_labels(self):
        """Get human-readable labels for selected fields (multi-source aware)"""
        labels = {}

        for field in self.selected_fields:
            # Parse field format: source__field_name or just field_name
            parts = field.split('__')

            if parts[0] in self.data_sources:
                # Multi-source format: source__field_name
                source = parts[0]
                field_key = '__'.join(parts[1:])
                fields_config = get_fields_for_source(source)
                label = fields_config.get(field_key, {}).get('label', field_key)
                # Prefix with source label for clarity
                source_label = REPORT_SCHEMA[source]['label']
                labels[field] = f"{source_label}: {label}"
            else:
                # Single source or primary source field
                fields_config = get_fields_for_source(self.primary_source)
                labels[field] = fields_config.get(field, {}).get('label', field)

        return labels

    def extract_values(self, obj):
        """Extract field values from a model instance (multi-source aware)"""
        values = {}

        for field in self.selected_fields:
            parts = field.split('__')
            value = obj

            # Check if field is from a secondary source
            if parts[0] in self.data_sources and parts[0] != self.primary_source:
                # Navigate to related source first
                source = parts[0]
                join_info = get_join_path(self.primary_source, source)

                if join_info:
                    join_path = join_info['path']
                    # Navigate through the join
                    for path_part in join_path.split('__'):
                        if value is None:
                            break
                        value = getattr(value, path_part, None)

                    # Handle M2M or reverse FK (may return queryset/manager)
                    if value is not None and hasattr(value, 'first'):
                        # Get first related object for M2M/reverse FK
                        value = value.first()

                    # Now navigate to the actual field
                    field_path = parts[1:]
                else:
                    # No join path found, set to None
                    value = None
                    field_path = []
            else:
                # Primary source field or single source
                if parts[0] in self.data_sources:
                    # Remove source prefix
                    field_path = parts[1:]
                else:
                    # No source prefix
                    field_path = parts

            # Navigate through field path
            for part in field_path:
                if value is None:
                    break
                value = getattr(value, part, None)

            # Format the value
            if value is None:
                values[field] = ''
            elif hasattr(value, 'strftime'):  # Date/DateTime
                if hasattr(value, 'hour'):
                    values[field] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    values[field] = value.strftime('%Y-%m-%d')
            elif isinstance(value, bool):
                values[field] = 'Yes' if value else 'No'
            else:
                values[field] = str(value)

        return values
