# Quick Start Guide

Get the DMP (Device Management Platform) up and running in minutes.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git (optional, for cloning)

## Development Setup

### 1. Clone or Download

```bash
# Using Git
git clone <repo-url>
cd it

# Or extract from archive to a directory
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000 in your browser.

## Key Features

- **Multi-source Custom Reports**: Combine data from Devices, Employees, Assignments, and Approvals
- **Dynamic Report Builder**: Select fields, apply filters, export to CSV/Excel/JSON/PDF
- **Approval Workflow**: Request-based approval system for device operations
- **SPA Architecture**: HTMX-powered single-page application
- **Responsive Design**: Mobile-first Bootstrap 5 UI

## Project Structure

```
it/
├── core/              # Core app (authentication, base templates)
├── devices/           # Device management
├── employees/         # Employee management
├── assignments/       # Device assignments
├── approvals/         # Approval workflow
├── reports/           # Dynamic reporting system
└── templates/         # Component-based SPA templates
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.2.1, Python 3.12 |
| Database | SQLite (dev), PostgreSQL (prod) |
| Frontend | Bootstrap 5, HTMX |
| Deployment | Docker, Traefik |

## Next Steps

- [Windows Installation](installation-windows.md) - For Windows users with batch scripts
- [Development Setup](development-setup.md) - Detailed development commands
- [Production Deployment](../deployment/production.md) - Docker deployment guide
