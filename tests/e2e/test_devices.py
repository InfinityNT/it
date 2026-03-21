"""
E2E tests for device management.

Tests device list loading, modals, and search filtering.
"""
import pytest
from playwright.sync_api import expect
from tests.e2e.helpers import wait_for_htmx_load, wait_for_htmx, open_modal, close_modal


@pytest.mark.e2e
class TestDeviceList:

    def test_device_page_loads(self, authenticated_page, server_url, sample_devices):
        """Device page loads with header and filter controls."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        expect(page.locator("text=Device Management")).to_be_visible()
        expect(page.locator("#device-filters")).to_be_visible()

    def test_device_list_loads_via_htmx(self, authenticated_page, server_url, sample_devices):
        """Device table loads via HTMX and shows test devices."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        wait_for_htmx_load(page, "#devices-table")
        expect(page.locator("text=LPT-001")).to_be_visible()
        expect(page.locator("text=LPT-002")).to_be_visible()

    def test_device_cards_show_info(self, authenticated_page, server_url, sample_devices):
        """Device entries display asset tag, serial number, and model."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        wait_for_htmx_load(page, "#devices-table")
        expect(page.locator("text=LPT-001")).to_be_visible()
        expect(page.locator("text=SN-TEST-001")).to_be_visible()
        expect(page.locator("text=Latitude 5540").first).to_be_visible()

    def test_device_search_filters_results(self, authenticated_page, server_url, sample_devices):
        """Typing in search input filters devices via HTMX."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        wait_for_htmx_load(page, "#devices-table")
        search_input = page.locator('#device-filters input[name="search"]')
        search_input.fill("LPT-001")
        wait_for_htmx(page)
        expect(page.locator("text=LPT-001")).to_be_visible()


@pytest.mark.e2e
class TestDeviceModals:

    def test_add_device_button_visible_for_admin(self, authenticated_page, server_url, sample_devices):
        """Admin user sees the Add Device button."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        expect(page.locator("text=Add Device").first).to_be_visible()

    def test_add_device_modal_opens(self, authenticated_page, server_url, sample_devices):
        """Clicking Add Device opens the modal with the form."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        wait_for_htmx_load(page, "#devices-table")
        open_modal(page, 'a.btn.btn-primary:has-text("Add Device")')
        modal = page.locator("#dynamicModal")
        expect(modal.locator("#asset_tag")).to_be_visible()

    def test_add_device_modal_closes(self, authenticated_page, server_url, sample_devices):
        """The add device modal can be closed."""
        page = authenticated_page
        page.goto(f"{server_url}/devices/")
        wait_for_htmx_load(page, "#devices-table")
        open_modal(page, 'a.btn.btn-primary:has-text("Add Device")')
        close_modal(page)
        expect(page.locator("#dynamicModal.show")).to_have_count(0)
