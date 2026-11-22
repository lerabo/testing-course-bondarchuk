"""Р-26: звіт про дисципліну - класи еквівалентності, межі і текст звіту."""

from datetime import date

import pytest

from student_portal.course_report import (
    CourseReport,
    course_report,
    final_grade,
    format_report,
)
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

D1 = date(2026, 10, 1)
D2 = date(2026, 10, 15)
D3 = date(2026, 11, 2)


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


def student(sid: int, first: str, last: str, *grades: Grade) -> Student:
    return Student(sid, first, last, list(grades))


def group_of(*students: Student) -> Group:
    group = Group("КН-11")
    for s in students:
        group.add(s)
    return group


def python(score: int, on: date = D1) -> Grade:
    return Grade("Python", score, on)


# --- зарахована оцінка (final_grade) ---


def test_final_grade_none_without_grades():
    assert final_grade(student(1, "Олена", "Коваль"), "Python") is None


def test_final_grade_ignores_other_courses():
    s = student(1, "Олена", "Коваль", Grade("Бази даних", 90, D1))
    assert final_grade(s, "Python") is None


def test_final_grade_single():
    assert final_grade(student(1, "Олена", "Коваль", python(88)), "Python").score == 88


def test_retake_with_later_date_wins():
    s = student(1, "Олена", "Коваль", python(40, D1), python(75, D2))
    assert final_grade(s, "Python").score == 75


def test_later_date_wins_even_if_added_earlier():
    """Порядок додавання не важливий, якщо дати різні: рішення - за датою."""
    s = student(1, "Олена", "Коваль", python(75, D2), python(40, D1))
    assert final_grade(s, "Python").score == 75


@known_defect("#59")
def test_same_date_later_added_wins():
    s = student(1, "Олена", "Коваль", python(40, D2), python(75, D2))
    assert final_grade(s, "Python").score == 75


# --- graded і average ---


def test_graded_counts_students_with_course_grade_only():
    group = group_of(
        student(1, "Олена", "Коваль", python(95), Grade("Бази даних", 70, D1)),
        student(2, "Андрій", "Мельник", Grade("Бази даних", 80, D1)),
        student(3, "Ірина", "Бойко", python(40, D1), python(75, D2)),
    )
    report = course_report(group, "Python")
    assert report.graded == 2


def test_average_uses_final_grades_only():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(40, D1), python(75, D2)),
    )
    assert course_report(group, "Python").average == 85.0


def test_average_is_rounded_to_one_decimal():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(75)),
        student(3, "Ірина", "Бойко", python(61)),
    )
    assert course_report(group, "Python").average == 77.0
    group.add(student(4, "Софія", "Ткачук", python(60)))
    assert course_report(group, "Python").average == 72.8


# --- pass_rate: межа 60 балів і знаменник ---


@pytest.mark.parametrize(("score", "rate"), [(59, 0), (61, 100), (100, 100), (0, 0)])
def test_pass_rate_boundary(score, rate):
    group = group_of(student(1, "Олена", "Коваль", python(score)))
    assert course_report(group, "Python").pass_rate == rate


@known_defect("#60")
def test_score_60_passes():
    group = group_of(student(1, "Олена", "Коваль", python(60)))
    assert course_report(group, "Python").pass_rate == 100


@pytest.mark.parametrize(
    ("scores", "rate"),
    [((95, 75, 40), 66), ((95, 40, 30), 33), ((95, 75), 100)],
)
def test_pass_rate_is_floor_of_percent(scores, rate):
    group = group_of(
        *(
            student(i, "Ім’я", f"Прізвище{i}", python(s))
            for i, s in enumerate(scores, 1)
        )
    )
    assert course_report(group, "Python").pass_rate == rate


@known_defect("#61")
def test_pass_rate_counts_only_graded_students():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(75)),
        student(3, "Ірина", "Бойко"),
    )
    assert course_report(group, "Python").pass_rate == 100


def test_retake_after_fail_counts_as_passed():
    group = group_of(student(1, "Олена", "Коваль", python(30, D1), python(70, D2)))
    report = course_report(group, "Python")
    assert report.pass_rate == 100
    assert report.debtors == []


# --- distribution і debtors ---


def test_distribution_in_ects_order_without_missing_letters():
    group = group_of(
        student(1, "Олена", "Коваль", python(10)),
        student(2, "Андрій", "Мельник", python(95)),
        student(3, "Ірина", "Бойко", python(78)),
        student(4, "Софія", "Ткачук", python(92)),
    )
    distribution = course_report(group, "Python").distribution
    assert list(distribution.items()) == [("A", 2), ("C", 1), ("Fx", 1)]


def test_distribution_counts_final_grade_letter():
    group = group_of(student(1, "Олена", "Коваль", python(20, D1), python(83, D2)))
    assert course_report(group, "Python").distribution == {"B": 1}


def test_zero_points_is_fx_debtor():
    group = group_of(student(1, "Олена", "Коваль", python(0)))
    report = course_report(group, "Python")
    assert report.distribution == {"Fx": 1}
    assert report.debtors == ["Коваль Олена"]


def test_debtors_in_id_order():
    group = group_of(
        student(3, "Ірина", "Бойко", python(30)),
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(15)),
    )
    assert course_report(group, "Python").debtors == ["Мельник Андрій", "Бойко Ірина"]


def test_report_without_grades_is_empty():
    group = group_of(student(1, "Олена", "Коваль", Grade("Бази даних", 90, D1)))
    assert course_report(group, "Python") == CourseReport("Python")


def test_report_for_empty_group_is_empty():
    assert course_report(Group("КН-12"), "Python") == CourseReport("Python")


# --- текст звіту ---


@known_defect("#60")
def test_text_from_specification():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(75)),
        student(3, "Ірина", "Бойко", python(60)),
    )
    assert format_report(course_report(group, "Python")) == (
        "Дисципліна: Python\n"
        "Оцінок: 3, середній бал: 76,7, склали: 100 %\n"
        "A: 1, C: 1, E: 1\n"
        "Боржники: немає"
    )


def test_text_with_debtors():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(15)),
        student(3, "Ірина", "Бойко", python(30)),
    )
    assert format_report(course_report(group, "Python")) == (
        "Дисципліна: Python\n"
        "Оцінок: 3, середній бал: 46,7, склали: 33 %\n"
        "A: 1, Fx: 2\n"
        "Боржники: Мельник Андрій, Бойко Ірина"
    )


def test_text_without_debtors_uses_decimal_comma():
    group = group_of(
        student(1, "Олена", "Коваль", python(95)),
        student(2, "Андрій", "Мельник", python(61)),
    )
    assert format_report(course_report(group, "Python")) == (
        "Дисципліна: Python\n"
        "Оцінок: 2, середній бал: 78,0, склали: 100 %\n"
        "A: 1, E: 1\n"
        "Боржники: немає"
    )


def test_text_without_grades():
    assert format_report(CourseReport("Python")) == "Дисципліна: Python\nОцінок немає"
