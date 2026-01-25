# Project Structure

Overview of the DMP codebase organization and key configuration.

## Directory Layout

```
it/
├── DMP/                   # Main Django project package
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI configuration for deployment
│   └── asgi.py            # ASGI configuration for async deployment
│
├── core/                  # Core app (authentication, base templates)
├── devices/               # Device management
├── employees/             # Employee management
├── assignments/           # Device assignments
├── approvals/             # Approval workflow
├── reports/               # Dynamic reporting system
│
├── templates/             # Component-based SPA templates
│   ├── base.html          # Single SPA base template
│   ├── login.html         # Authentication page
│   ├── pages/             # Main content pages
│   └── components/        # Reusable components
│
├── static/                # Static files (CSS, JS, images)
│
├── manage.py              # Django command-line utility
├── db.sqlite3             # SQLite database file (development)
├── requirements.txt       # Python dependencies
└── venv/                  # Python virtual environment
```

## Django Apps

| App | Purpose |
|-----|---------|
| `core` | Authentication, base templates, shared utilities |
| `devices` | Device models, views, and management |
| `employees` | Employee models and management |
| `assignments` | Device-to-employee assignments |
| `approvals` | Approval workflow for device operations |
| `reports` | Dynamic reporting and export system |

## Key Configuration

### settings.py

| Setting | Value | Notes |
|---------|-------|-------|
| Database | SQLite | Development default |
| Django version | 5.2.1 | |
| Python version | 3.12 | |
| Debug mode | Enabled | Disable in production |
| Time zone | UTC | |
| Static files | `/static/` | |

### URL Structure

```python
# Root URLs (DMP/urls.py)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('devices/', include('devices.urls')),
    path('employees/', include('employees.urls')),
    path('assignments/', include('assignments.urls')),
    path('approvals/', include('approvals.urls')),
    path('reports/', include('reports.urls')),
]
```

## Database Models

### Core Entities

- **Device**: IT assets with asset tags, serial numbers, models
- **Employee**: Staff members with departments and job titles
- **Assignment**: Links devices to employees with dates
- **ApprovalRequest**: Workflow for device operations

### Relationships

```
Device ←→ Assignment ←→ Employee
   ↓
ApprovalRequest (M2M through approval_requests.devices)
```

## Next Steps

- [Template System](template-system.md) - Component architecture
- [Development Setup](../getting-started/development-setup.md) - Commands
- [Custom Reports](../features/custom-reports.md) - Report builder
