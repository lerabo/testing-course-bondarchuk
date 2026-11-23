"""Тести за специфікацією Р-28 «Академічна довідка» (не за кодом модуля)."""

from datetime import date

import pytest

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.transcript import transcript

OCT = date(2026, 10, 1)
NOV = date(2026, 11, 1)
RULE = "-" * 50
HEADER = "Дисципліна             Кредити  Бали  ECTS  Оцінка"


def known_defect(issue: str):
    return pytest.mark.xfail(
        strict=True, raises=AssertionError, reason=f"відомий дефект {issue}"
    )


def lines_of(*grades: Grade, funding=Funding.BUDGET, group="КН-11") -> list[str]:
    student = Student(7, "Тарас", "Гнатюк", list(grades), funding=funding)
    return transcript(student, group).splitlines()


def table(lines: list[str]) -> list[str]:
    """Рядки дисциплін між другою і третьою лінією з дефісів."""
    start = lines.index(RULE)
    end = lines.index(RULE, start + 1)
    assert lines[start + 1] == HEADER
    return lines[start + 2 : end]


def expected_row(course: str, credits: int, score: int, letter: str, word: str):
    # ширина з Р-28: 22 ліворуч, 8, 6, 6 праворуч, два пробіли, оцінка
    return f"{course:<22}{credits:>8}{score:>6}{letter:>6}  {word}"


def summary_value(lines: list[str], prefix: str) -> str:
    [line] = [line for line in lines if line.startswith(prefix)]
    return line.removeprefix(prefix)


# --- Приклад зі специфікації ---------------------------------------------------


def test_example_from_specification():
    student = Student(
        1,
        "Олена",
        "Коваль",
        [Grade("Python", 95, OCT), Grade("Бази даних", 90, NOV)],
    )

    assert transcript(student, "КН-11") == (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Коваль Олена (id 1), група КН-11\n"
        "Форма навчання: державне замовлення\n"
        f"{RULE}\n"
        f"{HEADER}\n"
        "Python                       5    95     A  відмінно\n"
        "Бази даних                   4    90     A  відмінно\n"
        f"{RULE}\n"
        "Усього кредитів: 9\n"
        "Середній бал (зважений за кредитами): 92,8\n"
        "Боргів немає\n"
    )


def test_every_line_ends_with_newline():
    text = transcript(Student(7, "Тарас", "Гнатюк", [Grade("Python", 70, OCT)]))

    assert text.endswith("\n")
    assert "\n\n" not in text


# --- Заголовок ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("group", "expected"),
    [
        ("КН-11", "Студент: Гнатюк Тарас (id 7), група КН-11"),
        ("", "Студент: Гнатюк Тарас (id 7)"),
    ],
    ids=["with-group", "without-group"],
)
def test_student_line(group, expected):
    lines = lines_of(group=group)

    assert lines[:2] == ["АКАДЕМІЧНА ДОВІДКА", expected]


def test_default_group_is_empty():
    student = Student(7, "Тарас", "Гнатюк")

    assert transcript(student).splitlines()[1] == "Студент: Гнатюк Тарас (id 7)"


@pytest.mark.parametrize(
    ("funding", "expected"),
    [(Funding.BUDGET, "державне замовлення"), (Funding.CONTRACT, "контракт")],
    ids=["budget", "contract"],
)
def test_funding_line(funding, expected):
    assert lines_of(funding=funding)[2] == f"Форма навчання: {expected}"


def test_without_grades_only_no_grades_line_follows_header():
    assert lines_of() == [
        "АКАДЕМІЧНА ДОВІДКА",
        "Студент: Гнатюк Тарас (id 7), група КН-11",
        "Форма навчання: державне замовлення",
        "Оцінок немає",
    ]


# --- Таблиця ------------------------------------------------------------------


def test_table_framed_by_rules_with_header():
    lines = lines_of(Grade("Python", 95, OCT))

    assert lines[3:6] == [RULE, HEADER, expected_row("Python", 5, 95, "A", "відмінно")]
    assert lines[6] == RULE


def test_courses_sorted_by_name():
    courses = ["Веброзробка", "Python", "Алгоритми", "Бази даних", "Історія"]
    rows = table(lines_of(*(Grade(c, 80, OCT) for c in courses)))

    assert [row.split("  ")[0].rstrip() for row in rows] == sorted(courses)


def test_one_row_per_course_even_with_retakes():
    rows = table(
        lines_of(
            Grade("Python", 40, OCT),
            Grade("Python", 80, NOV),
            Grade("Алгоритми", 70, OCT),
        )
    )

    assert len(rows) == 2


# --- Зарахована оцінка --------------------------------------------------------


@pytest.mark.parametrize(
    "grades",
    [
        [Grade("Python", 40, OCT), Grade("Python", 80, NOV)],
        [Grade("Python", 80, NOV), Grade("Python", 40, OCT)],
    ],
    ids=["later-listed-last", "later-listed-first"],
)
def test_latest_grade_by_date_counts(grades):
    assert table(lines_of(*grades)) == [expected_row("Python", 5, 80, "C", "добре")]


def test_same_date_later_added_counts():
    rows = table(lines_of(Grade("Python", 55, NOV), Grade("Python", 85, NOV)))

    assert rows == [expected_row("Python", 5, 85, "B", "добре")]


def test_later_worse_grade_still_counts():
    rows = table(lines_of(Grade("Python", 95, OCT), Grade("Python", 61, NOV)))

    assert rows == [expected_row("Python", 5, 61, "E", "задовільно")]


# --- Кредити ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("course", "credits"),
    [
        ("Python", 5),
        ("Бази даних", 4),
        ("Алгоритми", 5),
        ("Веброзробка", 4),
        ("Фізкультура", 3),
        ("python", 3),  # назва з іншим регістром - інша дисципліна
    ],
)
def test_credits(course, credits):
    lines = lines_of(Grade(course, 80, OCT))

    assert table(lines) == [expected_row(course, credits, 80, "C", "добре")]
    assert summary_value(lines, "Усього кредитів: ") == str(credits)


# --- Шкала ECTS (Р-05): межі кожного класу --------------------------------------

ECTS_CASES = [
    (100, "A"),
    (90, "A"),
    (89, "B"),
    (82, "B"),
    (81, "C"),
    (75, "C"),
    (74, "D"),
    (67, "D"),
    (66, "E"),
    (60, "E"),
    (59, "Fx"),
    (35, "Fx"),
    (34, "Fx"),
    (0, "Fx"),
]


@pytest.mark.parametrize(("score", "letter"), ECTS_CASES)
def test_ects_letter(score, letter):
    [row] = table(lines_of(Grade("Python", score, OCT)))

    assert row[36:42] == f"{letter:>6}"


# --- Національна шкала - за літерою ------------------------------------------

NATIONAL_CASES = [
    (100, "відмінно"),
    (90, "відмінно"),  # A
    (89, "добре"),  # B
    (82, "добре"),
    (81, "добре"),  # C
    (75, "добре"),
    pytest.param(74, "задовільно", marks=known_defect("#93")),  # D
    (67, "задовільно"),
    (66, "задовільно"),  # E
    (60, "задовільно"),
    (59, "незадовільно"),  # Fx
    (0, "незадовільно"),
]


@pytest.mark.parametrize(("score", "word"), NATIONAL_CASES)
def test_national_grade(score, word):
    [row] = table(lines_of(Grade("Python", score, OCT)))

    assert row[42:] == f"  {word}"


# --- Підсумок -----------------------------------------------------------------


def test_total_credits_is_sum_of_courses():
    lines = lines_of(
        Grade("Python", 80, OCT),
        Grade("Бази даних", 80, OCT),
        Grade("Історія", 80, OCT),
    )

    assert summary_value(lines, "Усього кредитів: ") == "12"


def test_total_credits_count_course_once_with_retake():
    lines = lines_of(Grade("Python", 40, OCT), Grade("Python", 80, NOV))

    assert summary_value(lines, "Усього кредитів: ") == "5"


AVERAGE = "Середній бал (зважений за кредитами): "


@pytest.mark.parametrize(
    ("grades", "expected"),
    [
        # (94·5 + 84·3) / 8 = 90,25 → 90,3: половина вгору
        ([Grade("Python", 94, OCT), Grade("Історія", 84, OCT)], "90,3"),
        # (90·5 + 88·3) / 8 = 89,25 → 89,3
        ([Grade("Python", 90, OCT), Grade("Історія", 88, OCT)], "89,3"),
        # (95·5 + 90·4) / 9 = 92,777… → 92,8
        ([Grade("Python", 95, OCT), Grade("Бази даних", 90, OCT)], "92,8"),
        # (61·5 + 60·4) / 9 = 60,555… → 60,6;  зважене, а не просте 60,5
        ([Grade("Python", 61, OCT), Grade("Бази даних", 60, OCT)], "60,6"),
        # (70·3 + 71·3) / 6 = 70,5 - ціле і половина
        ([Grade("Історія", 70, OCT), Grade("Фізика", 71, OCT)], "70,5"),
        # рівно ціле: один знак після коми
        ([Grade("Python", 90, OCT)], "90,0"),
        # (80·3 + 81·3 + 81·3)/9 = 80,666… → 80,7
        (
            [
                Grade("Історія", 80, OCT),
                Grade("Фізика", 81, OCT),
                Grade("Хімія", 81, OCT),
            ],
            "80,7",
        ),
    ],
    ids=["90.25", "89.25", "92.78", "weighted", "70.5", "integer", "80.67"],
)
def test_weighted_average(grades, expected):
    assert summary_value(lines_of(*grades), AVERAGE) == expected


def test_average_uses_counted_grade_only():
    lines = lines_of(Grade("Python", 20, OCT), Grade("Python", 80, NOV))

    assert summary_value(lines, AVERAGE) == "80,0"


# --- Борги --------------------------------------------------------------------


def test_no_debts():
    assert lines_of(Grade("Python", 60, OCT))[-1] == "Боргів немає"


def test_debts_in_table_order():
    lines = lines_of(
        Grade("Веброзробка", 10, OCT),
        Grade("Бази даних", 95, OCT),
        Grade("Python", 59, OCT),
        Grade("Алгоритми", 0, OCT),
    )

    assert lines[-1] == "Борги: Python, Алгоритми, Веброзробка"


def test_debt_closed_by_later_grade():
    lines = lines_of(Grade("Python", 30, OCT), Grade("Python", 60, NOV))

    assert lines[-1] == "Боргів немає"


def test_later_failure_creates_debt():
    lines = lines_of(Grade("Python", 75, OCT), Grade("Python", 59, NOV))

    assert lines[-1] == "Борги: Python"
