"""
Helper utilities for E2E tests.
Handles HTMX content loading, Bootstrap modal interactions,
and authentication flow.
"""
from playwright.sync_api import Page, expect


def wait_for_htmx(page: Page, timeout: float = 10_000):
    """Wait for all in-flight HTMX requests to complete."""
    page.evaluate(
        """(timeout) => new Promise((resolve, reject) => {
            const indicator = document.querySelector('.htmx-request');
            if (!indicator) {
                setTimeout(resolve, 100);
                return;
            }
            const timer = setTimeout(() => {
                reject(new Error('HTMX settle timeout'));
            }, timeout);
            document.body.addEventListener('htmx:afterSettle', function handler() {
                clearTimeout(timer);
                document.body.removeEventListener('htmx:afterSettle', handler);
                setTimeout(resolve, 150);
            }, { once: true });
        })""",
        timeout,
    )


def wait_for_htmx_load(page: Page, selector: str, timeout: float = 10_000):
    """
    Wait for an element populated by HTMX hx-trigger='load' to have content.
    Waits until the selector contains non-empty content (spinner replaced).
    """
    page.wait_for_function(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            return el.children.length > 0
                && !el.querySelector('.spinner-border');
        }""",
        arg=selector,
        timeout=timeout,
    )


def login(page: Page, base_url: str, username: str, password: str):
    """
    Perform login through the actual login page UI.
    The login form POSTs via HTMX, then on success does:
        setTimeout(() => window.location.href = '/', 1000)
    So we wait for navigation to the dashboard.
    """
    page.goto(f"{base_url}/login/")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url(f"{base_url}/", timeout=15_000)


def open_modal(page: Page, trigger_selector: str):
    """
    Click a trigger element that opens a Bootstrap modal via HTMX,
    then wait for the modal to be fully visible with content loaded.
    """
    page.click(trigger_selector)
    page.wait_for_selector("#dynamicModal.show", state="visible", timeout=10_000)
    page.wait_for_function(
        """() => {
            const content = document.querySelector('#dynamicModalContent');
            return content && content.children.length > 0
                && !content.querySelector('.spinner-border');
        }""",
        timeout=10_000,
    )


def close_modal(page: Page):
    """Close the currently open dynamic modal."""
    page.click("#dynamicModal .btn-close")
    page.wait_for_selector("#dynamicModal.show", state="hidden", timeout=5_000)
