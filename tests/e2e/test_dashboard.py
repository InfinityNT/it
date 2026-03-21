"""
E2E tests for the dashboard page.

Tests that the dashboard loads with all HTMX-powered sections
and that navigation links work.
"""
import pytest
from playwright.sync_api import expect
from tests.e2e.helpers import wait_for_htmx_load


@pytest.mark.e2e
class TestDashboardLoad:

    def test_dashboard_has_quick_actions(self, authenticated_page, server_url):
        """Dashboard shows the Quick Actions section title."""
        page = authenticated_page
        expect(page.locator(".dashboard-container .section-title", has_text="Quick Actions")).to_be_visible()

    def test_dashboard_stats_load_via_htmx(self, authenticated_page, server_url):
        """Stats section loads asynchronously via HTMX."""
        page = authenticated_page
        wait_for_htmx_load(page, "#dashboard-stats")
        stats = page.locator("#dashboard-stats")
        expect(stats.locator(".spinner-border")).to_have_count(0)

    def test_dashboard_activity_loads_via_htmx(self, authenticated_page, server_url):
        """Activity feed loads asynchronously."""
        page = authenticated_page
        wait_for_htmx_load(page, "#dashboard-activity")
        activity = page.locator("#dashboard-activity")
        expect(activity.locator(".spinner-border")).to_have_count(0)

    def test_dashboard_quick_actions_load_via_htmx(self, authenticated_page, server_url):
        """Quick actions grid loads asynchronously."""
        page = authenticated_page
        wait_for_htmx_load(page, "#dashboard-quick-actions")
        qa = page.locator("#dashboard-quick-actions")
        expect(qa.locator(".spinner-border")).to_have_count(0)


@pytest.mark.e2e
class TestNavigation:

    def test_navbar_links_present_for_admin(self, authenticated_page, server_url):
        """Admin user sees all navigation links in the navbar."""
        page = authenticated_page
        nav = page.locator("#navbarNav")
        expect(nav.locator("text=Dashboard")).to_be_visible()
        expect(nav.locator("text=Devices")).to_be_visible()
        expect(nav.locator("text=Assignments")).to_be_visible()

    def test_navigate_to_devices(self, authenticated_page, server_url):
        """Clicking Devices in navbar navigates to /devices/."""
        page = authenticated_page
        page.click("#navbarNav >> text=Devices")
        expect(page).to_have_url(f"{server_url}/devices/")
        expect(page.locator("text=Device Management")).to_be_visible(timeout=10_000)

    def test_navigate_to_employees(self, authenticated_page, server_url):
        """Clicking Employees in navbar navigates to /employees/."""
        page = authenticated_page
        page.click("#navbarNav >> text=Employees")
        expect(page).to_have_url(f"{server_url}/employees/")
