"""Характеризаційний тест: поточна поведінка transcript() перед рефакторингом.

Знімок фіксує, що модуль робить зараз, разом із дефектами. Входи - файли даних
і власні випадки за гілками старої функції та межами обох шкал (техніка ЛР 3).
Дати задано явно: за замовчуванням Grade бере date.today().
"""

from datetime import date
from pathlib import Path

import pytest

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.storage import load_group
from student_portal.transcript import transcript

DATA = Path(__file__).resolve().parents[2] / "data"
OCT = date(2026, 10, 1)
NOV = date(2026, 11, 1)
DEC = date(2026, 12, 1)

# Межі шкали ECTS (90, 82, 75, 67, 60) і старого коду (35 - «FX»/«F»,
# 74 - «добре»/«задовільно»): значення на межі й по обидва боки від неї
BOUNDARY_SCORES = [100, 90, 89, 82, 81, 75, 74, 73, 67, 66, 60, 59, 35, 34, 0]

CASES = {
    "no-grades": [],
    "one-course": [Grade("Python", 95, OCT)],
    # кредити: усі дисципліни довідника і дві, яких у ньому немає (3 кредити)
    "all-credits": [
        Grade("Python", 90, OCT),
        Grade("Бази даних", 82, OCT),
        Grade("Алгоритми", 75, OCT),
        Grade("Веброзробка", 67, OCT),
        Grade("Фізкультура", 60, OCT),
        Grade("Англійська мова", 100, OCT),
    ],
    # порядок у списку не за назвами: таблиця має бути відсортована
    "unsorted-courses": [
        Grade("Веброзробка", 80, OCT),
        Grade("Python", 70, OCT),
        Grade("Алгоритми", 91, OCT),
        Grade("Бази даних", 85, OCT),
    ],
    # перескладання: незадовільно, потім пізніша оцінка
    "retake-later": [
        Grade("Python", 40, OCT),
        Grade("Python", 78, NOV),
    ],
    # пізніша дата стоїть у списку раніше
    "retake-later-listed-first": [
        Grade("Python", 78, NOV),
        Grade("Python", 40, OCT),
    ],
    # однакова дата: має зараховуватися додана пізніше (Р-26)
    "retake-same-date": [
        Grade("Python", 55, NOV),
        Grade("Python", 85, NOV),
    ],
    "three-grades-last-not-best": [
        Grade("Python", 95, OCT),
        Grade("Python", 30, DEC),
        Grade("Python", 70, NOV),
    ],
    # середній бал з точною половиною десятої: (94·5 + 84·3) / 8 = 90,25
    "average-90.25": [Grade("Python", 94, OCT), Grade("Фізкультура", 84, OCT)],
    # (90·5 + 88·3) / 8 = 89,25
    "average-89.25": [Grade("Python", 90, OCT), Grade("Фізкультура", 88, OCT)],
    # (95·5 + 90·4) / 9 = 92,777…
    "average-92.78": [Grade("Python", 95, OCT), Grade("Бази даних", 90, OCT)],
    "several-debts": [
        Grade("Алгоритми", 12, OCT),
        Grade("Python", 59, OCT),
        Grade("Бази даних", 95, OCT),
        Grade("Веброзробка", 34, OCT),
    ],
    "debt-closed-by-retake": [
        Grade("Алгоритми", 50, OCT),
        Grade("Алгоритми", 64, NOV),
        Grade("Python", 20, OCT),
    ],
}

# Межі обох шкал - кожна окремим знімком, щоб назва тесту вказувала на бал;
# назви випадків латиницею: pytest екранує кирилицю в ідентифікаторах тестів
CASES |= {f"score-{score}": [Grade("Python", score, OCT)] for score in BOUNDARY_SCORES}


@pytest.mark.parametrize("case", list(CASES))
def test_case(snapshot, case):
    student = Student(7, "Тарас", "Гнатюк", CASES[case])

    assert transcript(student, "КН-11") == snapshot


@pytest.mark.parametrize(
    ("funding", "group_name", "grades"),
    [
        (Funding.BUDGET, "", []),
        (Funding.CONTRACT, "", []),
        (Funding.CONTRACT, "КН-11", []),
        (Funding.CONTRACT, "", [Grade("Python", 61, OCT)]),
    ],
    ids=[
        "budget-no-group",
        "contract-no-group",
        "contract-group",
        "contract-no-group-graded",
    ],
)
def test_header(snapshot, funding, group_name, grades):
    student = Student(12, "Ірина", "Шевчук", grades, funding=funding)

    assert transcript(student, group_name) == snapshot


@pytest.mark.parametrize("file", ["group.json", "stream.json"])
def test_data_file(snapshot, file):
    group = load_group(DATA / file)

    assert "\n".join(transcript(s, group.name) for s in group) == snapshot
