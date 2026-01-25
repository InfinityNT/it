# AI Assistant Guide

This document provides guidance to AI assistants when working with code in this repository.

## Project Overview

This is a Django 5.2.1 project named "DMP" (Device Management Platform) using Python 3.12. It's an IT asset management system with:

- Device tracking and management
- Employee management
- Device assignments workflow
- Approval workflow for operations
- Dynamic reporting system
- Component-based SPA architecture

## Key Principles

### Code Quality

- Follow Django best practices and PEP 8 style guide
- Use descriptive variable and function names
- Keep functions focused and single-purpose
- Document complex logic with comments
- Write tests for new functionality

### Template Architecture

This project uses a component-based SPA architecture with HTMX:

- **Single Base Template**: `base.html` handles all page layouts
- **Component-Based**: Reusable components via `{% include %}`
- **Modal Forms**: Form interactions via overlay modals
- **HTMX Integration**: Dynamic content loading without page refreshes

### Design Patterns

- **Builder Pattern**: `DynamicReportQueryBuilder` for query construction
- **Strategy Pattern**: Different formatters for output types
- **Schema-Driven UI**: Field schema defines available options

## Tracking Changes

**Important**: Keep track of all changes in `docs/CHANGELOG.md`:

- Document every modification
- Follow semantic versioning
- Group changes by type (Added, Changed, Fixed, Removed)

## Common Tasks

### Running the Development Server

```bash
source venv/bin/activate  # macOS/Linux
python manage.py runserver
```

### Database Operations

```bash
python manage.py migrate          # Apply migrations
python manage.py makemigrations   # Create migrations
python manage.py createsuperuser  # Create admin user
```

### Database Reset & Maintenance

```bash
# Reset database (preserving users and reference data)
python manage.py reset_database --keep-users --keep-reference-data

# Full reset with data regeneration
python manage.py reset_database --regenerate

# Check and fix data integrity
python manage.py check_data_integrity --fix

# Setup groups and permissions
python manage.py setup_groups

# Generate sample data
python manage.py create_predefined_data
python manage.py generate_sample_devices --count 50
```

### Testing

```bash
python manage.py test             # Run all tests
python manage.py test <app_name>  # Test specific app
```

## File Locations

| Category | Location |
|----------|----------|
| Django settings | `DMP/settings.py` |
| URL configuration | `DMP/urls.py` |
| Templates | `templates/` |
| Static files | `static/` and `*/static/` |
| Models | `*/models.py` |
| Views | `*/views.py` |

## Django Apps

| App | Purpose |
|-----|---------|
| `core` | Authentication, base templates |
| `devices` | Device management |
| `employees` | Employee management |
| `assignments` | Device assignments |
| `approvals` | Approval workflow |
| `reports` | Dynamic reporting |

## ORM Optimization Tips

1. **select_related**: For forward FK/OneToOne
2. **prefetch_related**: For reverse FK/M2M
3. **annotate**: For aggregates (Count, Sum, Avg)
4. **Q objects**: For complex filtering

## Template Conventions

- Use `{% include %}` for reusable components
- Use HTMX attributes for dynamic loading:
  - `hx-get` - Load content
  - `hx-target` - Target element
  - `hx-push-url` - Update browser URL

## Completed Modernizations

### Template Architecture (Completed)

- Component directory structure created
- Single base template consolidated
- Navigation components extracted
- Form pages converted to modals
- 41 obsolete templates archived

### Migration Squash (Completed)

- All 40 migrations squashed to clean initial migrations
- Fixed circular dependency between `core` and `employees` apps
- Migration dependency chain:
  1. `employees` - Foundation (no dependencies)
  2. `core` - Depends on employees
  3. `devices` - Depends on core, employees
  4. `approvals` - Depends on devices
  5. `assignments` - Depends on devices, employees, approvals
  6. `reports` - Standalone

## Additional Resources

- [Project Structure](../architecture/project-structure.md)
- [Template System](../architecture/template-system.md)
- [Development Setup](../getting-started/development-setup.md)
- [Testing Guide](../testing/guide.md)
