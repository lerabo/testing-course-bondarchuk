"""Дата перескладання (вимога Р-21)."""

from datetime import date, timedelta

MIN_DAYS_AFTER_EXAM = 7
SATURDAY = 5


def retake_date(exam_date: date, semester_end: date, holidays=()) -> date:
    candidate = exam_date + timedelta(days=MIN_DAYS_AFTER_EXAM)
    while candidate.weekday() >= SATURDAY or candidate in holidays:
        candidate += timedelta(days=1)
    return candidate
