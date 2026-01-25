# Development Setup

Detailed development environment setup and common commands.

## Virtual Environment

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

## Django Management Commands

### Server Operations

```bash
# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Run accessible from network
python manage.py runserver 0.0.0.0:8000
```

### Database Operations

```bash
# Run migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Show migration status
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser
```

### Database Reset

```bash
# Full database reset (deletes all data)
python manage.py reset_database

# Reset but keep user accounts
python manage.py reset_database --keep-users

# Reset but keep users and reference data (categories, manufacturers, etc.)
python manage.py reset_database --keep-users --keep-reference-data

# Reset and regenerate sample data
python manage.py reset_database --regenerate

# Reset for CI/testing (no confirmation prompt)
python manage.py reset_database --no-confirm --regenerate
```

### Data Generation

```bash
# Set up user groups and permissions
python manage.py setup_groups

# Create predefined manufacturers, vendors, categories
python manage.py create_predefined_data

# Generate sample devices (default: 50)
python manage.py generate_sample_devices --count 100

# Generate sample employees (default: 50)
python manage.py populate_mock_data --count 100
```

### Database Maintenance

```bash
# Check data integrity
python manage.py check_data_integrity

# Fix data integrity issues
python manage.py check_data_integrity --fix

# Backup database
python manage.py backup_database --compress

# Restore database
python manage.py restore_database backup_file.tar.gz

# Optimize database (vacuum, analyze)
python manage.py optimize_database
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test <app_name>

# Run with verbosity
python manage.py test -v 2
```

### Static Files

```bash
# Collect static files for production
python manage.py collectstatic

# Clear and recollect
python manage.py collectstatic --clear
```

### Django Shell

```bash
# Interactive Django shell
python manage.py shell

# Database shell
python manage.py dbshell
```

## Key Configuration

| Setting | Value |
|---------|-------|
| Database | SQLite (development) |
| Django version | 5.2.1 |
| Debug mode | Enabled |
| Time zone | UTC |
| Static files URL | `/static/` |

## Project Structure

```
DMP/
├── settings.py     # Django configuration
├── urls.py         # Root URL configuration
├── wsgi.py         # WSGI configuration for deployment
└── asgi.py         # ASGI configuration for async deployment
```

## Tracking Changes

- Keep track of all changes in `CHANGELOG.md`
- Always document every modification
- Follow semantic versioning for releases

## Next Steps

- [Project Structure](../architecture/project-structure.md) - Codebase organization
- [Template System](../architecture/template-system.md) - Component architecture
- [Testing Guide](../testing/guide.md) - Testing procedures
