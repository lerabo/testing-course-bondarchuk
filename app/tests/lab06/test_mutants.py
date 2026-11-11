"""Тести, що вбивають живих мутантів базової лінії (ЛР 6, завдання 2)."""

from datetime import date

import pytest

from student_portal.corrections import correct_grade
from student_portal.exceptions import CorrectionPeriodError
from student_portal.grades import Grade


def test_period_error_message_names_last_correction_day():
    # Р-08: строк - 14 календарних днів включно, тож для оцінки від 01.10.2026
    # повідомлення має назвати 15.10.2026 (вбиває мутантів 7 і 9 corrections.py).
    grade = Grade("Python", 70, date(2026, 10, 1))
    with pytest.raises(CorrectionPeriodError, match=r"до 15\.10\.2026 включно"):
        correct_grade(grade, 75, today=date(2026, 10, 21))
