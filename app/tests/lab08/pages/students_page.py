"""Список студентів (Р-25): таблиця, пошук, додавання і видалення."""

import re

from playwright.sync_api import Locator, Page, expect

from .student_card import StudentCard


class StudentsPage:
    """Список студентів групи для адміністратора і викладача."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.heading = page.get_by_role("heading", name="Студенти групи")
        self.search = page.get_by_label("Пошук за прізвищем")
        self.rows = page.locator("#students tr")
        self.total = page.locator("#total")
        self.empty = page.get_by_text("Нікого не знайдено")
        self.add_form = page.get_by_role("heading", name="Новий студент")
        self.last_name = page.get_by_label("Прізвище", exact=True)
        self.first_name = page.get_by_label("Ім’я")
        self.email = page.get_by_label("Email")
        self.add = page.get_by_role("button", name="Додати студента")
        self.delete_buttons = page.get_by_role("button", name="Видалити")
        self.message = page.get_by_role("status")
        self.error = page.get_by_role("alert")

    def wait_loaded(self) -> "StudentsPage":
        """Список завантажено: лічильник показує число."""
        expect(self.total).to_have_text(re.compile(r"Усього: \d+"))
        return self

    def row_for(self, text: str) -> Locator:
        return self.rows.filter(has_text=text)

    def email_of(self, text: str) -> Locator:
        return self.row_for(text).locator("td").nth(1)

    def average_of(self, text: str) -> Locator:
        return self.row_for(text).locator("td").nth(2)

    def search_for(self, text: str) -> "StudentsPage":
        self.search.fill(text)
        return self

    def add_student(self, last_name: str, first_name: str, email: str) -> None:
        self.last_name.fill(last_name)
        self.first_name.fill(first_name)
        self.email.fill(email)
        self.add.click()

    def delete(self, text: str, *, accept: bool) -> list[str]:
        """Натискає «Видалити» і відповідає на підтвердження; повертає текст діалогу."""
        messages: list[str] = []

        def answer(dialog):
            messages.append(dialog.message)
            dialog.accept() if accept else dialog.dismiss()

        self.page.once("dialog", answer)
        self.row_for(text).get_by_role("button", name="Видалити").click()
        return messages

    def open_card(self, text: str) -> StudentCard:
        self.row_for(text).get_by_role("link").click()
        return StudentCard(self.page).wait_loaded()
