"""Р-21: дата перескладання (розроблено через TDD)."""

from datetime import date

from student_portal.retake import retake_date

SEMESTER_END = date(2026, 12, 31)


def test_monday_exam_gives_monday_next_week():
    assert retake_date(date(2026, 11, 9), SEMESTER_END) == date(2026, 11, 16)


def test_wednesday_exam_gives_wednesday_next_week():
    assert retake_date(date(2026, 11, 11), SEMESTER_END) == date(2026, 11, 18)


def test_saturday_moves_to_monday():
    assert retake_date(date(2026, 11, 14), SEMESTER_END) == date(2026, 11, 23)
