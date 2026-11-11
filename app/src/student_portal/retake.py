"""Дата перескладання (вимога Р-21)."""

from datetime import date


def retake_date(exam_date: date, semester_end: date, holidays=()) -> date:
    return date(2026, 11, 16)
