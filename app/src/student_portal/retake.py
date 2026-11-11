"""Дата перескладання (вимога Р-21)."""

from collections.abc import Container
from datetime import date, timedelta

from student_portal.exceptions import PortalError

MIN_DAYS_AFTER_EXAM = 7
SATURDAY = 5


class NoRetakeDateError(PortalError):
    """Перескладання не вміщується в семестр."""


def is_working_day(day: date, holidays: Container[date]) -> bool:
    return day.weekday() < SATURDAY and day not in holidays


def retake_date(
    exam_date: date, semester_end: date, holidays: Container[date] = ()
) -> date:
    candidate = exam_date + timedelta(days=MIN_DAYS_AFTER_EXAM)
    while not is_working_day(candidate, holidays):
        candidate += timedelta(days=1)
    if candidate > semester_end:
        raise NoRetakeDateError(
            f"немає дати перескладання до кінця семестру {semester_end:%d.%m.%Y}"
        )
    return candidate
