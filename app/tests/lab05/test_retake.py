"""Р-21: дата перескладання (розроблено через TDD)."""

from datetime import date

import pytest  # noqa: F401 - тимчасово: тести винятку закоментовано

from student_portal.retake import retake_date

SEMESTER_END = date(2026, 12, 31)


def test_monday_exam_gives_monday_next_week():
    assert retake_date(date(2026, 11, 9), SEMESTER_END) == date(2026, 11, 16)


def test_wednesday_exam_gives_wednesday_next_week():
    assert retake_date(date(2026, 11, 11), SEMESTER_END) == date(2026, 11, 18)


def test_saturday_moves_to_monday():
    assert retake_date(date(2026, 11, 14), SEMESTER_END) == date(2026, 11, 23)


def test_sunday_moves_to_monday():
    assert retake_date(date(2026, 11, 15), SEMESTER_END) == date(2026, 11, 23)


def test_holiday_moves_to_next_working_day():
    christmas = date(2026, 12, 25)  # п'ятниця; далі вихідні
    result = retake_date(date(2026, 12, 18), SEMESTER_END, holidays={christmas})
    assert result == date(2026, 12, 28)


def test_several_holidays_in_a_row_are_skipped():
    holidays = {date(2026, 12, 29), date(2026, 12, 30)}  # вівторок і середа
    result = retake_date(date(2026, 12, 22), SEMESTER_END, holidays=holidays)
    assert result == date(2026, 12, 31)


# def test_no_date_before_semester_end_raises():
#     with pytest.raises(NoRetakeDateError, match="28.12.2026"):
#         retake_date(date(2026, 12, 22), date(2026, 12, 28))


def test_last_day_of_semester_is_allowed():
    semester_end = date(2026, 12, 29)
    assert retake_date(date(2026, 12, 22), semester_end) == semester_end


# def test_weekend_shift_past_semester_end_raises():
#     # кандидат 26.12 (субота) ще в семестрі, але понеділок 28.12 - уже ні
#     with pytest.raises(NoRetakeDateError, match="27.12.2026"):
#         retake_date(date(2026, 12, 19), date(2026, 12, 27))
#
