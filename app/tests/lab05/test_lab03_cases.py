"""Тестові випадки ЛР 3 (Р-08, Р-17, Р-18), автоматизовані параметризованими тестами.

Ідентифікатори наборів даних збігаються з таблицями docs/lab03/.
Відомі дефекти позначено xfail(strict=True) з номером issue з ЛР 4.
"""

from datetime import date, timedelta

import pytest

from student_portal.corrections import correct_grade
from student_portal.exceptions import (
    CorrectionPeriodError,
    InvalidGradeError,
    InvalidTransitionError,
)
from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.scholarship import Scholarship, scholarship
from student_portal.status import Event, Status

GRADED_ON = date(2026, 10, 1)


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


def make_grade() -> Grade:
    return Grade("Python", 70, GRADED_ON)


# ---------------------------------------------------------------- Р-08


@pytest.mark.parametrize(
    ("days", "score"),
    [
        pytest.param(4, 75, id="TB-EP-01"),
        pytest.param(4, 0, id="TB-BVA-02"),
        pytest.param(4, 100, id="TB-BVA-03"),
        pytest.param(0, 75, id="TB-BVA-05"),
        pytest.param(13, 75, id="TB-BVA-06"),
        pytest.param(14, 75, id="TB-BVA-07", marks=known_defect("#14")),
    ],
)
def test_correction_accepted(days, score):
    # Arrange
    grade = make_grade()
    today = GRADED_ON + timedelta(days=days)
    # Act
    corrected = correct_grade(grade, score, today=today)
    # Assert
    assert corrected == Grade("Python", score, GRADED_ON)
    assert grade.score == 70


@pytest.mark.parametrize(
    ("days", "score"),
    [
        pytest.param(-1, 75, id="TB-EP-02", marks=known_defect("#18")),
        pytest.param(20, 75, id="TB-EP-03"),
        pytest.param(20, 150, id="TB-EP-08"),
        pytest.param(15, 75, id="TB-BVA-08"),
    ],
)
def test_correction_outside_period_rejected(days, score):
    # Arrange
    grade = make_grade()
    today = GRADED_ON + timedelta(days=days)
    # Act / Assert
    with pytest.raises(CorrectionPeriodError):
        correct_grade(grade, score, today=today)
    assert grade.score == 70


@pytest.mark.parametrize(
    "score",
    [
        pytest.param(-10, id="TB-EP-04"),
        pytest.param(150, id="TB-EP-05"),
        pytest.param(75.5, id="TB-EP-06", marks=known_defect("#19")),
        pytest.param("75", id="TB-EP-07", marks=known_defect("#19")),
        pytest.param(-1, id="TB-BVA-01"),
        pytest.param(101, id="TB-BVA-04"),
    ],
)
def test_correction_invalid_score_rejected(score):
    # Arrange
    grade = make_grade()
    today = GRADED_ON + timedelta(days=4)
    # Act / Assert
    with pytest.raises(InvalidGradeError):
        correct_grade(grade, score, today=today)
    assert grade.score == 70


# ---------------------------------------------------------------- Р-17

FX_AND_HIGH_AVERAGE = [59] + [100] * 9  # середній 95,9


@pytest.mark.parametrize(
    ("funding", "scores", "expected"),
    [
        pytest.param(Funding.BUDGET, [], Scholarship.NONE, id="TB-DT-01"),
        pytest.param(Funding.BUDGET, [70], Scholarship.NONE, id="TB-DT-02"),
        pytest.param(Funding.BUDGET, [80], Scholarship.REGULAR, id="TB-DT-03"),
        pytest.param(Funding.BUDGET, [95], Scholarship.INCREASED, id="TB-DT-04"),
        pytest.param(Funding.BUDGET, [50, 70], Scholarship.NONE, id="TB-DT-05"),
        pytest.param(Funding.BUDGET, [55, 100], Scholarship.NONE, id="TB-DT-06"),
        pytest.param(
            Funding.BUDGET,
            FX_AND_HIGH_AVERAGE,
            Scholarship.NONE,
            id="TB-DT-07",
            marks=known_defect("#15"),
        ),
        pytest.param(Funding.CONTRACT, [], Scholarship.NONE, id="TB-DT-08"),
        pytest.param(Funding.CONTRACT, [70], Scholarship.NONE, id="TB-DT-09"),
        pytest.param(Funding.CONTRACT, [80], Scholarship.NONE, id="TB-DT-10"),
        pytest.param(Funding.CONTRACT, [95], Scholarship.NONE, id="TB-DT-11"),
        pytest.param(Funding.CONTRACT, [50, 70], Scholarship.NONE, id="TB-DT-12"),
        pytest.param(Funding.CONTRACT, [55, 100], Scholarship.NONE, id="TB-DT-13"),
        pytest.param(
            Funding.CONTRACT, FX_AND_HIGH_AVERAGE, Scholarship.NONE, id="TB-DT-14"
        ),
        pytest.param(Funding.BUDGET, [90], Scholarship.INCREASED, id="TB-DT-15"),
        pytest.param(Funding.BUDGET, [89, 90], Scholarship.REGULAR, id="TB-DT-16"),
        pytest.param(Funding.BUDGET, [75], Scholarship.REGULAR, id="TB-DT-17"),
        pytest.param(Funding.BUDGET, [74, 75], Scholarship.NONE, id="TB-DT-18"),
    ],
)
def test_scholarship_decision_table(funding, scores, expected):
    # Arrange
    grades = [Grade(f"Дисципліна {i}", score) for i, score in enumerate(scores)]
    student = Student(1, "Олена", "Коваль", grades, funding=funding)
    # Act
    result = scholarship(student)
    # Assert
    assert result == expected


# ---------------------------------------------------------------- Р-18


@pytest.mark.parametrize(
    ("steps", "expected_statuses"),
    [
        pytest.param(
            [
                Event.TAKE_LEAVE,
                Event.RETURN,
                Event.EXPEL,
                Event.REINSTATE,
                Event.GRADUATE,
            ],
            [
                Status.ON_LEAVE,
                Status.ACTIVE,
                Status.EXPELLED,
                Status.ACTIVE,
                Status.GRADUATED,
            ],
            id="TB-ST-01",
        ),
        pytest.param(
            [Event.TAKE_LEAVE, Event.EXPEL],
            [Status.ON_LEAVE, Status.EXPELLED],
            id="TB-ST-02",
        ),
    ],
)
def test_valid_transition_sequence(steps, expected_statuses):
    # Arrange
    student = Student(1, "Олена", "Коваль")
    student.add_grade(Grade("Python", 80))
    # Act
    statuses = [student.change_status(event) for event in steps]
    # Assert
    assert statuses == expected_statuses
    assert [g.score for g in student.grades] == [80]


def test_graduate_with_fx_rejected():  # TB-ST-03: умова переходу хибна
    # Arrange
    student = Student(1, "Олена", "Коваль")
    student.add_grade(Grade("Python", 40))
    # Act / Assert
    with pytest.raises(InvalidTransitionError):
        student.change_status(Event.GRADUATE)
    assert student.status == Status.ACTIVE


ADD_GRADE = "виставити оцінку"


@pytest.mark.parametrize(
    ("status", "event"),
    [
        pytest.param(Status.ACTIVE, Event.RETURN, id="TB-ST-04"),
        pytest.param(Status.ACTIVE, Event.REINSTATE, id="TB-ST-05"),
        pytest.param(Status.ON_LEAVE, Event.TAKE_LEAVE, id="TB-ST-06"),
        pytest.param(Status.ON_LEAVE, Event.REINSTATE, id="TB-ST-07"),
        pytest.param(Status.ON_LEAVE, Event.GRADUATE, id="TB-ST-08"),
        pytest.param(
            Status.ON_LEAVE, ADD_GRADE, id="TB-ST-09", marks=known_defect("#17")
        ),
        pytest.param(Status.EXPELLED, Event.TAKE_LEAVE, id="TB-ST-10"),
        pytest.param(Status.EXPELLED, Event.RETURN, id="TB-ST-11"),
        pytest.param(Status.EXPELLED, Event.EXPEL, id="TB-ST-12"),
        pytest.param(Status.EXPELLED, Event.GRADUATE, id="TB-ST-13"),
        pytest.param(Status.EXPELLED, ADD_GRADE, id="TB-ST-14"),
        pytest.param(Status.GRADUATED, Event.TAKE_LEAVE, id="TB-ST-15"),
        pytest.param(Status.GRADUATED, Event.RETURN, id="TB-ST-16"),
        pytest.param(
            Status.GRADUATED, Event.EXPEL, id="TB-ST-17", marks=known_defect("#16")
        ),
        pytest.param(Status.GRADUATED, Event.REINSTATE, id="TB-ST-18"),
        pytest.param(Status.GRADUATED, Event.GRADUATE, id="TB-ST-19"),
        pytest.param(
            Status.GRADUATED, ADD_GRADE, id="TB-ST-20", marks=known_defect("#17")
        ),
    ],
)
def test_invalid_transition_rejected(status, event):
    # Arrange
    student = Student(1, "Олена", "Коваль", [Grade("Python", 85)], status=status)
    # Act / Assert
    with pytest.raises(InvalidTransitionError):
        if event == ADD_GRADE:
            student.add_grade(Grade("Python", 80))
        else:
            student.change_status(event)
    assert student.status == status
    assert [g.score for g in student.grades] == [85]
