"""
E2E tests for authentication flows.

Tests login, logout, and auth redirect behavior.
"""
import pytest
from playwright.sync_api import expect
from tests.e2e.helpers import login


@pytest.mark.e2e
class TestLogin:

    def test_login_page_loads(self, page, server_url):
        """The login page renders with the form and branding."""
        page.goto(f"{server_url}/login/")
        expect(page.locator(".login-header h1")).to_contain_text("Welcome back")
        expect(page.locator("#username")).to_be_visible()
        expect(page.locator("#password")).to_be_visible()
        expect(page.locator("#login-btn")).to_be_visible()

    def test_login_success_redirects_to_dashboard(self, page, server_url, admin_user):
        """Valid credentials redirect to the dashboard."""
        login(page, server_url, "testadmin", "testpass123")
        expect(page).to_have_url(f"{server_url}/")

    def test_login_invalid_credentials_shows_error(self, page, server_url, admin_user):
        """Invalid password shows error alert without page navigation."""
        page.goto(f"{server_url}/login/")
        page.fill("#username", "testadmin")
        page.fill("#password", "wrongpassword")
        page.click("#login-btn")
        error_alert = page.locator("#error-alert")
        expect(error_alert).to_be_visible(timeout=5_000)
        expect(page).to_have_url(f"{server_url}/login/")

    def test_login_empty_form_stays_on_page(self, page, server_url):
        """Submitting empty form triggers browser validation."""
        page.goto(f"{server_url}/login/")
        page.click("#login-btn")
        expect(page).to_have_url(f"{server_url}/login/")


@pytest.mark.e2e
class TestAuthRedirect:

    def test_unauthenticated_root_redirects_to_login(self, page, server_url):
        """Visiting / without auth redirects to /login/."""
        page.goto(f"{server_url}/")
        expect(page).to_have_url(f"{server_url}/login/?next=/")

    def test_unauthenticated_devices_redirects_to_login(self, page, server_url):
        """Visiting /devices/ without auth redirects to /login/."""
        page.goto(f"{server_url}/devices/")
        expect(page).to_have_url(f"{server_url}/login/?next=/devices/", timeout=5_000)


@pytest.mark.e2e
class TestLogout:

    def test_logout_redirects_to_login(self, authenticated_page, server_url):
        """Submitting logout form returns user to login page."""
        page = authenticated_page
        # Sidebar may be hidden on desktop viewport; submit the form directly
        page.evaluate("document.getElementById('logout-form').submit()")
        expect(page).to_have_url(f"{server_url}/login/", timeout=10_000)

    def test_after_logout_cannot_access_dashboard(self, authenticated_page, server_url):
        """After logout, visiting / redirects back to login."""
        page = authenticated_page
        page.evaluate("document.getElementById('logout-form').submit()")
        expect(page).to_have_url(f"{server_url}/login/", timeout=10_000)
        page.goto(f"{server_url}/")
        expect(page).to_have_url(f"{server_url}/login/?next=/")
