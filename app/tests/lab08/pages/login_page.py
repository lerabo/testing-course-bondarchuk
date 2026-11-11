"""Сторінка входу (Р-25)."""

from playwright.sync_api import Page


class LoginPage:
    """Форма входу з токеном і шапка з роллю та кнопкою «Вийти»."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.token = page.get_by_label("Токен")
        self.submit = page.get_by_role("button", name="Увійти")
        self.error = page.get_by_role("alert")
        self.role = page.locator("#role")
        self.logout = page.get_by_role("button", name="Вийти")

    def open(self) -> "LoginPage":
        self.page.goto(f"{self.base_url}/")
        return self

    def login(self, token: str) -> "LoginPage":
        self.token.fill(token)
        self.submit.click()
        return self
