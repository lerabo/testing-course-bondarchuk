"""Властивості Р-21 (retake_date) і Р-17 (scholarship), перевірені Hypothesis."""

from contextlib import suppress
from datetime import date, timedelta

import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.retake import NoRetakeDateError, retake_date
from student_portal.scholarship import Scholarship, scholarship

# ------------------------------------------------------------------ Р-21


@st.composite
def retake_inputs(draw):
    """Іспит у 2026-2027 роках, кінець семестру за 0-60 днів, свята поруч."""
    exam = draw(st.dates(date(2026, 1, 1), date(2027, 12, 31)))
    semester_end = exam + timedelta(days=draw(st.integers(0, 60)))
    near = st.dates(exam, exam + timedelta(days=60))
    holidays = draw(st.frozensets(near, max_size=10))
    return exam, semester_end, holidays


def oracle(exam, semester_end, holidays):
    """Еталон: простий перебір днів від exam + 7 до кінця семестру."""
    day = exam + timedelta(days=7)
    while day <= semester_end:
        if day.weekday() < 5 and day not in holidays:
            return day
        day += timedelta(days=1)
    return None


@given(retake_inputs())
def test_retake_matches_brute_force_oracle(inputs):
    exam, semester_end, holidays = inputs
    expected = oracle(exam, semester_end, holidays)
    if expected is None:
        with pytest.raises(NoRetakeDateError):
            retake_date(exam, semester_end, holidays)
    else:
        assert retake_date(exam, semester_end, holidays) == expected


@given(retake_inputs(), st.integers(1, 30))
def test_longer_semester_keeps_retake_date(inputs, extra_days):
    # Метаморфна: якщо дата є, подовження семестру її не змінює.
    exam, semester_end, holidays = inputs
    try:
        result = retake_date(exam, semester_end, holidays)
    except NoRetakeDateError:
        assume(False)
    longer = semester_end + timedelta(days=extra_days)
    assert retake_date(exam, longer, holidays) == result


@given(retake_inputs(), st.integers(0, 30))
def test_holiday_after_retake_date_changes_nothing(inputs, offset):
    # Метаморфна: свято після знайденої дати не впливає на результат,
    # а свято саме в цей день переносить перескладання пізніше.
    exam, semester_end, holidays = inputs
    try:
        result = retake_date(exam, semester_end, holidays)
    except NoRetakeDateError:
        assume(False)
    later = result + timedelta(days=offset + 1)
    assert retake_date(exam, semester_end, holidays | {later}) == result
    with suppress(NoRetakeDateError):
        assert retake_date(exam, semester_end, holidays | {result}) > result


# ------------------------------------------------------------------ Р-17

RANK = {Scholarship.NONE: 0, Scholarship.REGULAR: 1, Scholarship.INCREASED: 2}
scores = st.integers(0, 100)


def student_with(score_list, funding=Funding.BUDGET):
    grades = [Grade(f"Дисципліна {i}", s) for i, s in enumerate(score_list)]
    return Student(1, "Олена", "Коваль", grades, funding=funding)


@pytest.mark.xfail(strict=True, reason="відомий дефект #15")
@given(debt=st.integers(0, 59), high=st.lists(st.integers(90, 100), min_size=5))
@example(debt=59, high=[90, 91, 100, 100, 100])
def test_student_with_fx_gets_no_scholarship(debt, high):
    # Інваріант. Стратегія побудована за класом еквівалентності правила П8
    # таблиці рішень ЛР 3: одна Fx і середній бал не нижче 90.
    student = student_with([debt, *high])
    assume(student.average() >= 90)
    assert scholarship(student) == Scholarship.NONE


@given(st.lists(scores, max_size=12))
def test_contract_student_never_gets_scholarship(score_list):
    # Інваріант: на контракті стипендії немає за будь-яких оцінок.
    student = student_with(score_list, funding=Funding.CONTRACT)
    assert scholarship(student) == Scholarship.NONE


@given(st.lists(scores, min_size=1, max_size=12), st.data())
def test_better_worst_grade_never_lowers_scholarship(score_list, data):
    # Монотонність: заміна найгіршої оцінки кращою не знижує стипендію.
    worst = min(score_list)
    better = data.draw(st.integers(worst, 100), label="better")
    improved = list(score_list)
    improved[improved.index(worst)] = better
    before = scholarship(student_with(score_list))
    after = scholarship(student_with(improved))
    assert RANK[after] >= RANK[before]
