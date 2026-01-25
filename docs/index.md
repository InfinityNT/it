# DMP Documentation

Welcome to the Device Management Platform documentation.

## Quick Links

- [Quick Start Guide](getting-started/quick-start.md)
- [Windows Installation](getting-started/installation-windows.md)
- [Production Deployment](deployment/production.md)
- [Testing Guide](testing/guide.md)

## Documentation Sections

### Getting Started
- [Quick Start](getting-started/quick-start.md) - Get up and running in minutes
- [Windows Installation](getting-started/installation-windows.md) - Windows-specific setup with batch scripts
- [Development Setup](getting-started/development-setup.md) - Local development environment and commands

### Architecture
- [Project Structure](architecture/project-structure.md) - Codebase organization and key configuration
- [Template System](architecture/template-system.md) - Component-based SPA templates with HTMX

### Features
- [Custom Reports](features/custom-reports.md) - Multi-source dynamic report builder
- [Responsive Design](features/responsive-design.md) - Mobile UI implementation

### Operations
- [Production Deployment](deployment/production.md) - Docker & Traefik setup
- [Testing Guide](testing/guide.md) - Testing procedures and checklists

### Contributing
- [AI Assistant Guide](contributing/ai-assistant-guide.md) - Guidelines for AI assistants

### Reference
- [Changelog](CHANGELOG.md) - Version history and changes

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.2.1, Python 3.12 |
| Database | SQLite (dev), PostgreSQL (prod) |
| Frontend | Bootstrap 5, HTMX |
| Deployment | Docker, Traefik |

## Key Features

- **Multi-source Custom Reports** - Combine Devices, Employees, Assignments, Approvals
- **Approval Workflow** - Request-based approval system for device operations
- **SPA Architecture** - HTMX-powered single-page application
- **Responsive Design** - Mobile-first Bootstrap 5 UI
