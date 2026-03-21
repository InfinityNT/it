"""
Conftest for E2E tests.

Provides:
- DEBUG-only runtime guard
- Django live server + Playwright browser integration
- Test data factory fixtures
- Authenticated browser page fixture
"""
import os
import pytest

# Playwright uses greenlet which Django 5.x detects as async context.
# This is safe for tests — the live_server runs in a separate thread.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


# ── Safety Guard ──────────────────────────────────────────────

def pytest_configure(config):
    """Abort the test run if DEBUG is not True."""
    import django
    django.setup()
    from django.conf import settings
    if not settings.DEBUG:
        raise pytest.UsageError(
            "E2E tests require DEBUG=True. "
            "Refusing to run against a production-like environment."
        )


# ── Database config ──────────────────────────────────────────

@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    """
    Use a file-based SQLite test DB instead of in-memory.
    The live_server runs in a separate thread, and SQLite in-memory
    databases lock under concurrent HTMX requests. File-based SQLite
    handles this correctly.
    """
    from django.conf import settings as django_settings
    django_settings.DATABASES["default"].setdefault("TEST", {})
    django_settings.DATABASES["default"]["TEST"]["NAME"] = os.path.join(
        django_settings.BASE_DIR, "test_db.sqlite3"
    )


# ── Database fixtures ────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    """
    Create an admin/manager test user with full permissions.
    Sets password_change_required=False and password_changed_at
    to bypass PasswordChangeRequired and PasswordExpiry middleware.
    """
    from core.models import User
    from django.utils import timezone

    user = User.objects.create_user(
        username="testadmin",
        password="testpass123",
        first_name="Test",
        last_name="Admin",
        email="admin@test.com",
        is_staff=True,
        is_superuser=True,
    )
    user.password_change_required = False
    user.password_changed_at = timezone.now()
    user.save()
    return user


@pytest.fixture
def staff_user(db):
    """Create a non-superuser staff test user."""
    from core.models import User
    from django.utils import timezone

    user = User.objects.create_user(
        username="teststaff",
        password="testpass123",
        first_name="Test",
        last_name="Staff",
        email="staff@test.com",
    )
    user.password_change_required = False
    user.password_changed_at = timezone.now()
    user.save()
    return user


@pytest.fixture
def sample_devices(db, admin_user):
    """
    Create a minimal set of test devices.
    Returns a dict with the created objects for assertion use.
    """
    from devices.models import DeviceCategory, DeviceModel, Device

    category = DeviceCategory.objects.create(
        name="Laptop",
        description="Laptop computers",
        is_active=True,
    )

    device_model = DeviceModel.objects.create(
        category=category,
        manufacturer="Dell",
        model_name="Latitude 5540",
        specifications={"CPUModel": "Intel i7", "RAM": "16GB"},
        is_active=True,
    )

    available_device = Device.objects.create(
        asset_tag="LPT-001",
        serial_number="SN-TEST-001",
        hostname="LPT-001",
        device_model=device_model,
        status="available",
    )

    assigned_device = Device.objects.create(
        asset_tag="LPT-002",
        serial_number="SN-TEST-002",
        hostname="LPT-002",
        device_model=device_model,
        status="assigned",
    )

    return {
        "category": category,
        "device_model": device_model,
        "available_device": available_device,
        "assigned_device": assigned_device,
    }


# ── Playwright integration ────────────────────────────────────

@pytest.fixture
def server_url(live_server):
    """Return the live server URL for Playwright navigation."""
    return live_server.url


@pytest.fixture
def authenticated_page(page, server_url, admin_user):
    """
    A Playwright page already logged in as the admin user.
    Uses the real login UI flow.
    """
    from tests.e2e.helpers import login
    login(page, server_url, "testadmin", "testpass123")
    return page
