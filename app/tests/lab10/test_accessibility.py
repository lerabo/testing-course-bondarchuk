"""Доступність вебінтерфейсу: axe-core (WCAG 2.2 AA) і клавіатура (НФ-доступність)."""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

AXE_JS = Path(__file__).with_name("axe.min.js")
WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def log_in(page: Page, base_url: str, token: str) -> None:
    page.goto(base_url)
    page.get_by_label("Токен").fill(token)
    page.get_by_role("button", name="Увійти").click()


def axe_violations(page: Page) -> list[dict]:
    """Порушення WCAG 2.2 AA: правило, вплив, критерії і елементи."""
    if not AXE_JS.exists():
        pytest.fail(f"немає {AXE_JS.name}: завантажте axe-core 4.14 (README ЛР 10)")
    page.add_script_tag(content=AXE_JS.read_text())
    result = page.evaluate("(tags) => axe.run({runOnly: tags})", WCAG_AA)
    return [
        {
            "id": v["id"],
            "impact": v["impact"],
            "wcag": [t for t in v["tags"] if t.startswith("wcag") and t[4].isdigit()],
            "targets": [node["target"][0] for node in v["nodes"]],
        }
        for v in result["violations"]
    ]


def open_list(page: Page, base_url: str, token: str) -> None:
    log_in(page, base_url, token)
    expect(page.get_by_role("heading", name="Студенти групи")).to_be_visible()
    expect(page.locator("#students tr").first).to_be_visible()


def open_card(page: Page, base_url: str, token: str) -> None:
    if token.startswith("student-"):
        log_in(page, base_url, token)
    else:
        open_list(page, base_url, token)
        page.get_by_role("link", name="Коваль Олена").click()
    expect(page.locator("#card-name")).to_have_text("Коваль Олена")


def test_login_view_has_no_violations(page: Page, base_url):
    page.goto(base_url)

    assert axe_violations(page) == []


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="відомий дефект #80")
def test_admin_list_has_no_violations(page: Page, base_url):
    open_list(page, base_url, "admin-token")

    assert axe_violations(page) == []


def test_teacher_list_has_no_violations(page: Page, base_url):
    open_list(page, base_url, "teacher-token")

    assert axe_violations(page) == []


@pytest.mark.parametrize("token", ["admin-token", "teacher-token", "student-1-token"])
def test_card_has_no_violations(page: Page, base_url, token):
    open_card(page, base_url, token)

    assert axe_violations(page) == []


# --- Клавіатура: знайдена вручну проблема, якої axe не бачить -----------------


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="відомий дефект #81")
def test_sort_by_average_with_keyboard(page: Page, base_url):
    open_list(page, base_url, "teacher-token")
    page.locator("#search").focus()

    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement.textContent.trim()")

    assert focused == "Середній бал"
    page.keyboard.press("Enter")
    expect(page.locator("#sort-average")).to_have_attribute("aria-sort", "descending")
