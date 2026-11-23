# Тести pytest для вимоги Р-28 "Академічна довідка" (student_portal.transcript.transcript).
# Перевіряють лише те, що прямо сказано у вимозі. Код модуля для них не потрібен.
# Очікуваний вигляд рядків таблиці будується за шириною стовпців із вимоги:
# назва 22 (ліворуч), кредити 8, бали 6, ECTS 6 (праворуч), далі два пробіли й оцінка.

from datetime import date

import pytest

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.transcript import transcript

DASHES = "-" * 50
HEADER = f"{'Дисципліна':<22}{'Кредити':>8}{'Бали':>6}{'ECTS':>6}  Оцінка"
D1 = date(2026, 1, 10)
D2 = date(2026, 2, 10)
D3 = date(2026, 3, 10)


def make_student(grades=None, funding=Funding.BUDGET, sid=1,
                 first_name="Олена", last_name="Коваль"):
    return Student(sid, first_name, last_name,
                   grades=list(grades or []), funding=funding)


def row(name, credits, score, letter, national):
    return f"{name:<22}{credits:>8}{score:>6}{letter:>6}  {national}"


def lines_of(text):
    return text.split("\n")[:-1]


# ---------- Приклад із вимоги (точний збіг) ----------

def test_example_from_requirement_exact():
    student = make_student([
        Grade("Python", 95, D1),
        Grade("Бази даних", 90, D1),
    ])
    expected = (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Коваль Олена (id 1), група КН-11\n"
        "Форма навчання: державне замовлення\n"
        "--------------------------------------------------\n"
        "Дисципліна             Кредити  Бали  ECTS  Оцінка\n"
        "Python                       5    95     A  відмінно\n"
        "Бази даних                   4    90     A  відмінно\n"
        "--------------------------------------------------\n"
        "Усього кредитів: 9\n"
        "Середній бал (зважений за кредитами): 92,8\n"
        "Боргів немає\n"
    )
    assert transcript(student, "КН-11") == expected


# ---------- Кожен рядок закінчується символом нового рядка ----------

@pytest.mark.parametrize("grades", [[], [Grade("Python", 95, D1)]])
def test_every_line_ends_with_newline(grades):
    text = transcript(make_student(grades))
    assert text.endswith("\n")
    assert "\r" not in text
    assert all(line != "" for line in lines_of(text))


# ---------- Заголовок ----------

def test_header_without_group_by_default():
    lines = lines_of(transcript(make_student(sid=7)))
    assert lines[0] == "АКАДЕМІЧНА ДОВІДКА"
    assert lines[1] == "Студент: Коваль Олена (id 7)"


def test_header_with_empty_group_explicit():
    lines = lines_of(transcript(make_student(sid=7), ""))
    assert lines[1] == "Студент: Коваль Олена (id 7)"


def test_header_with_group():
    student = make_student(sid=42, first_name="Іван", last_name="Петренко")
    lines = lines_of(transcript(student, group_name="КН-21"))
    assert lines[1] == "Студент: Петренко Іван (id 42), група КН-21"


def test_funding_budget():
    lines = lines_of(transcript(make_student(funding=Funding.BUDGET)))
    assert lines[2] == "Форма навчання: державне замовлення"


def test_funding_contract():
    lines = lines_of(transcript(make_student(funding=Funding.CONTRACT)))
    assert lines[2] == "Форма навчання: контракт"


# ---------- Без оцінок ----------

def test_no_grades_only_message_after_header():
    text = transcript(make_student([], funding=Funding.CONTRACT, sid=3), "КН-11")
    assert text == (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Коваль Олена (id 3), група КН-11\n"
        "Форма навчання: контракт\n"
        "Оцінок немає\n"
    )


# ---------- Таблиця ----------

def test_table_structure():
    lines = lines_of(transcript(make_student([Grade("Python", 95, D1)])))
    assert lines[3] == DASHES
    assert lines[4] == HEADER
    assert lines[5] == row("Python", 5, 95, "A", "відмінно")
    assert lines[6] == DASHES


def test_disciplines_sorted_by_name_as_sorted():
    names = ["Фізика", "Python", "Веброзробка", "Алгоритми", "Інформатика", "Бази даних"]
    grades = [Grade(n, 90, D1) for n in names]
    lines = lines_of(transcript(make_student(grades)))
    table_names = [line[:22].rstrip() for line in lines[5:5 + len(names)]]
    assert table_names == sorted(names)
    # Порівнюються рядки, а не алфавіт за локаллю: «І» (U+0406) стоїть перед «А» (U+0410)
    assert table_names == ["Python", "Інформатика", "Алгоритми",
                           "Бази даних", "Веброзробка", "Фізика"]
    assert lines[5 + len(names)] == DASHES


# ---------- Кредити ЄКТС ----------

@pytest.mark.parametrize("course, credits", [
    ("Python", 5),
    ("Бази даних", 4),
    ("Алгоритми", 5),
    ("Веброзробка", 4),
    ("Фізика", 3),
    ("Історія України", 3),
])
def test_credits_per_course(course, credits):
    lines = lines_of(transcript(make_student([Grade(course, 95, D1)])))
    assert lines[5] == row(course, credits, 95, "A", "відмінно")
    assert f"Усього кредитів: {credits}" in lines


def test_total_credits_sum():
    grades = [Grade(n, 90, D1) for n in
              ["Python", "Алгоритми", "Бази даних", "Веброзробка", "Фізика"]]
    lines = lines_of(transcript(make_student(grades)))
    assert "Усього кредитів: 21" in lines


# ---------- Літера ECTS і національна шкала (межі Р-05) ----------

@pytest.mark.parametrize("score, letter, national", [
    (100, "A", "відмінно"), (90, "A", "відмінно"),
    (89, "B", "добре"), (82, "B", "добре"),
    (81, "C", "добре"), (75, "C", "добре"),
    (74, "D", "задовільно"), (67, "D", "задовільно"),
    (66, "E", "задовільно"), (60, "E", "задовільно"),
    (59, "Fx", "незадовільно"), (0, "Fx", "незадовільно"),
])
def test_ects_letter_and_national_scale(score, letter, national):
    lines = lines_of(transcript(make_student([Grade("Фізика", score, D1)])))
    assert lines[5] == row("Фізика", 3, score, letter, national)


# ---------- Вибір зарахованої оцінки ----------

def test_latest_by_date_wins_regardless_of_order():
    grades = [
        Grade("Python", 60, D3),
        Grade("Python", 95, D1),
        Grade("Python", 80, D2),
    ]
    lines = lines_of(transcript(make_student(grades)))
    assert lines[5] == row("Python", 5, 60, "E", "задовільно")
    assert lines[6] == DASHES  # одна дисципліна - один рядок


def test_same_date_later_added_wins():
    grades = [
        Grade("Python", 95, D2),
        Grade("Python", 70, D2),
        Grade("Python", 100, D1),
    ]
    lines = lines_of(transcript(make_student(grades)))
    assert lines[5] == row("Python", 5, 70, "D", "задовільно")


def test_only_counted_grade_used_in_average_and_debts():
    grades = [Grade("Фізика", 40, D1), Grade("Фізика", 85, D2)]
    lines = lines_of(transcript(make_student(grades)))
    assert lines[5] == row("Фізика", 3, 85, "B", "добре")
    assert "Середній бал (зважений за кредитами): 85,0" in lines
    assert lines[-1] == "Боргів немає"


# ---------- Середній бал ----------

@pytest.mark.parametrize("py, phys, expected", [
    (91, 89, "90,3"),   # 722/8 = 90,25 -> половина вгору
    (71, 69, "70,3"),   # 562/8 = 70,25 -> половина вгору
    (92, 87, "90,1"),   # 721/8 = 90,125 -> 90,1
    (95, 95, "95,0"),   # ціле значення, округлене до десятих
])
def test_weighted_average_rounding(py, phys, expected):
    grades = [Grade("Python", py, D1), Grade("Фізика", phys, D1)]
    lines = lines_of(transcript(make_student(grades)))
    assert f"Середній бал (зважений за кредитами): {expected}" in lines


def test_summary_order_after_table():
    grades = [Grade("Python", 95, D1), Grade("Бази даних", 90, D1)]
    lines = lines_of(transcript(make_student(grades)))
    assert lines[-4] == DASHES
    assert lines[-3] == "Усього кредитів: 9"
    assert lines[-2] == "Середній бал (зважений за кредитами): 92,8"
    assert lines[-1] == "Боргів немає"


# ---------- Борги ----------

def test_debts_listed_in_table_order():
    grades = [
        Grade("Фізика", 50, D1),
        Grade("Python", 95, D1),
        Grade("Алгоритми", 40, D1),
    ]
    lines = lines_of(transcript(make_student(grades)))
    assert lines[-1] == "Борги: Алгоритми, Фізика"


def test_single_debt():
    lines = lines_of(transcript(make_student([Grade("Python", 59, D1)])))
    assert lines[-1] == "Борги: Python"


def test_no_debts_when_lowest_is_e():
    lines = lines_of(transcript(make_student([Grade("Python", 60, D1)])))
    assert lines[-1] == "Боргів немає"
