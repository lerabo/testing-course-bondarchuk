"""Дата перескладання (вимога Р-21)."""

from datetime import date, timedelta

MIN_DAYS_AFTER_EXAM = 7


def retake_date(exam_date: date, semester_end: date, holidays=()) -> date:
    return exam_date + timedelta(days=MIN_DAYS_AFTER_EXAM)
