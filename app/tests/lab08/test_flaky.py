"""Експеримент з нестабільністю: наївна перевірка проти web-first assertion."""

import os

import pytest
from playwright.sync_api import expect

from .pages.login_page import LoginPage
from .pages.students_page import StudentsPage


def add(page, base_url, email):
    LoginPage(page, base_url).open().login("admin-token")
    students = StudentsPage(page).wait_loaded()
    students.add_student("Нестабільний", "Тест", email)
    return students


@pytest.mark.skipif(
    not os.environ.get("FLAKY_DEMO"), reason="демонстрація нестабільності: FLAKY_DEMO=1"
)
@pytest.mark.parametrize("attempt", range(20))
def test_naive_text_right_after_click(page, base_url, attempt):
    students = add(page, base_url, f"naive{attempt}@students.example.edu")

    assert students.message.text_content() == "Студента додано: Нестабільний Тест"


@pytest.mark.skipif(
    not os.environ.get("FLAKY_DEMO"), reason="демонстрація нестабільності: FLAKY_DEMO=1"
)
@pytest.mark.parametrize("attempt", range(20))
def test_web_first_assertion(page, base_url, attempt):
    students = add(page, base_url, f"wait{attempt}@students.example.edu")

    expect(students.message).to_have_text("Студента додано: Нестабільний Тест")
