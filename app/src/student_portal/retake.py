"""Дата перескладання (вимога Р-21)."""

from datetime import date, timedelta


def retake_date(exam_date: date, semester_end: date, holidays=()) -> date:
    return exam_date + timedelta(days=7)
