"""Дата перескладання (вимога Р-21)."""

from collections.abc import Container
from datetime import date, timedelta

MIN_DAYS_AFTER_EXAM = 7
SATURDAY = 5


def is_working_day(day: date, holidays: Container[date]) -> bool:
    return day.weekday() < SATURDAY and day not in holidays


def retake_date(
    exam_date: date, semester_end: date, holidays: Container[date] = ()
) -> date:
    candidate = exam_date + timedelta(days=MIN_DAYS_AFTER_EXAM)
    while not is_working_day(candidate, holidays):
        candidate += timedelta(days=1)
    return candidate
