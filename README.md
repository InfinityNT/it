# DMP - Device Management Platform

Django-based IT asset management system for tracking devices, employees, assignments, and approvals.

## Documentation

**[Full Documentation](docs/index.md)**

### Quick Links

- [Quick Start Guide](docs/getting-started/quick-start.md)
- [Windows Installation](docs/getting-started/installation-windows.md)
- [Production Deployment](docs/deployment/production.md)
- [Changelog](docs/CHANGELOG.md)

## Features

- **Multi-source Custom Reports** - Combine Devices, Employees, Assignments, Approvals
- **Approval Workflow** - Request-based approval system for device operations
- **SPA Architecture** - HTMX-powered single-page application
- **Responsive Design** - Mobile-first Bootstrap 5 UI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.2.1, Python 3.12 |
| Database | SQLite (dev), PostgreSQL (prod) |
| Frontend | Bootstrap 5, HTMX |
| Deployment | Docker, Traefik |

## Quick Start

```bash
# Clone and setup
git clone <repo-url> && cd it
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Visit http://localhost:8000

## Project Structure

```
it/
├── core/        # Authentication, base templates
├── devices/     # Device management
├── employees/   # Employee management
├── assignments/ # Device assignments
├── approvals/   # Approval workflow
├── reports/     # Dynamic reporting
├── templates/   # Component-based SPA templates
└── docs/        # Full documentation
```

## Documentation Structure

```
docs/
├── index.md                    # Documentation hub
├── getting-started/            # Setup guides
├── architecture/               # Codebase structure
├── deployment/                 # Production deployment
├── features/                   # Feature documentation
├── testing/                    # Testing procedures
├── contributing/               # Development guidelines
└── CHANGELOG.md                # Version history
```
