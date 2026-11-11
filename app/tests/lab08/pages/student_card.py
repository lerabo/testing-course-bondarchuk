"""Картка студента (Р-25): дані, оцінки і форма нової оцінки."""

import re

from playwright.sync_api import Page, expect


class StudentCard:
    """Картка студента: ім'я, середній бал, оцінки, нова оцінка, «До списку»."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.name = page.locator("#card-name")
        self.average = page.locator("#card-average")
        self.grades = page.locator("#grades tr")
        self.grade_form = page.get_by_role("heading", name="Нова оцінка")
        self.course = page.get_by_label("Дисципліна")
        self.score = page.get_by_label("Бали")
        self.submit_grade = page.get_by_role("button", name="Виставити")
        self.back = page.get_by_role("button", name="До списку")
        self.message = page.get_by_role("status")
        self.error = page.get_by_role("alert")

    def wait_loaded(self) -> "StudentCard":
        """Картку відкрито: заголовок з ім'ям і середній бал заповнено."""
        expect(self.name).to_have_text(re.compile(r"\S"))
        expect(self.average).to_have_text(re.compile(r"\S"))
        return self

    def grade_row(self, course: str):
        return self.grades.filter(has_text=course)

    def add_grade(self, course: str, score: int) -> None:
        self.course.fill(course)
        self.score.fill(str(score))
        self.submit_grade.click()
