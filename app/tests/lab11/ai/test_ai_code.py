# Тести для student_portal/transcript.py (вимога Р-28).
#
# Модуль перенесено зі старої системи деканату «майже без змін». Тому ці тести
# здебільшого характеризаційні: вони фіксують поточну поведінку функції
# transcript(), щоб подальший рефакторинг (технічний борг C901) нічого не зламав.
# Кілька місць виглядають підозріло, і тести навмисно закріплюють їх такими, як є.
# Перше: межі шкали ECTS і національної шкали не збігаються. Бал 74 дає ECTS "D",
# але національну оцінку "добре". Друге: дисципліни сортуються за кодами Unicode,
# а не за українським алфавітом. Латиниця йде перед кирилицею, а "І" (U+0406)
# стоїть перед "А" (U+0410), тому "Історія" опиняється раніше за "Алгоритми".
# Третє: середній бал округлюється «половина вгору», а не банківським способом.
# Якщо щось із цього вирішать виправити, відповідні тести треба оновити свідомо.
# Окремо варто знати, що group_name=None призведе до TypeError під час конкатенації.
# Цей випадок тут не закріплено, бо це радше дефект, ніж очікувана поведінка.

from datetime import date

import pytest

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.transcript import transcript

# ЗМІНЕНО (ЛР 11): CREDITS і W - внутрішні назви старого модуля, після рефакторингу
# їх немає; значення взято з Р-28, щоб решта тестів збиралася
CREDITS = {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}
W = 50


D1 = date(2025, 1, 15)
D2 = date(2025, 6, 20)
D3 = date(2025, 12, 1)


def make_student(grades=(), funding=Funding.BUDGET, sid=7):
    # Список оцінок передаємо завжди явно, бо в Student змінюваний аргумент за
    # замовчуванням grades=[] і стан міг би «протекти» між тестами.
    return Student(
        sid,
        "Іван",
        "Петренко",
        grades=list(grades),
        email=None,
        funding=funding,
    )


def row_for(text, course):
    # Рядок таблиці має фіксовані колонки: назва 22, кредити 8, бали 6, ECTS 6,
    # далі два пробіли й національна оцінка. Повертаємо розібрані колонки.
    prefix = course.ljust(22)
    lines = [ln for ln in text.splitlines() if ln.startswith(prefix)]
    assert len(lines) == 1, f"рядок для {course!r} не знайдено або він не один"
    line = lines[0]
    return {
        "course": line[:22].rstrip(),
        "credits": line[22:30].strip(),
        "score": line[30:36].strip(),
        "ects": line[36:42].strip(),
        "national": line[42:],
        "raw": line,
    }


# ---------------------------------------------------------------------------
# Заголовок довідки: ПІБ, id, група, форма фінансування
# ---------------------------------------------------------------------------


def test_no_grades_full_output_without_group():
    result = transcript(make_student())
    assert result == (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Петренко Іван (id 7)\n"
        "Форма навчання: державне замовлення\n"
        "Оцінок немає\n"
    )


def test_no_grades_with_group_and_contract():
    result = transcript(make_student(funding=Funding.CONTRACT), "КН-41")
    assert result == (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Петренко Іван (id 7), група КН-41\n"
        "Форма навчання: контракт\n"
        "Оцінок немає\n"
    )


def test_no_grades_output_has_no_table_or_summary():
    result = transcript(make_student())
    assert "-" * W not in result
    assert "Усього кредитів" not in result
    assert "Середній бал" not in result
    assert "Борги" not in result
    assert "Боргів немає" not in result


def test_empty_group_name_explicitly_is_same_as_default():
    student = make_student([Grade("Python", 90, D1)])
    assert transcript(student, "") == transcript(student)
    assert ", група" not in transcript(student, "")


def test_group_shown_when_grades_present():
    result = transcript(make_student([Grade("Python", 90, D1)]), "КН-41")
    assert result.splitlines()[1] == "Студент: Петренко Іван (id 7), група КН-41"


def test_default_funding_is_budget():
    student = Student(1, "Олена", "Коваль", grades=[])
    assert "Форма навчання: державне замовлення\n" in transcript(student)


@pytest.mark.parametrize(
    "funding, label",
    [
        (Funding.BUDGET, "державне замовлення"),
        (Funding.CONTRACT, "контракт"),
    ],
)
def test_funding_label(funding, label):
    result = transcript(make_student([Grade("Python", 90, D1)], funding=funding))
    assert result.splitlines()[2] == f"Форма навчання: {label}"


def test_student_id_is_converted_to_string():
    result = transcript(make_student(sid=12345))
    assert "(id 12345)" in result


# ---------------------------------------------------------------------------
# Повний вивід із таблицею (точне форматування колонок)
# ---------------------------------------------------------------------------


def test_full_transcript_exact_output():
    student = make_student(
        [
            Grade("Бази даних", 50, D1),
            Grade("Python", 95, D1),
            Grade("Історія", 74, D2),
        ],
        funding=Funding.CONTRACT,
    )
    # Порядок за кодами Unicode: Python (латиниця), Історія (І = U+0406), Бази даних.
    # Середній бал: (95*5 + 74*3 + 50*4) / 12 = 897 / 12 = 74.75, що дає 74,8.
    expected = (
        "АКАДЕМІЧНА ДОВІДКА\n"
        "Студент: Петренко Іван (id 7), група КН-41\n"
        "Форма навчання: контракт\n"
        + "-" * 50 + "\n"
        + "Дисципліна" + " " * 12 + " Кредити" + "  Бали" + "  ECTS" + "  Оцінка\n"
        + "Python" + " " * 16 + " " * 7 + "5" + " " * 4 + "95" + " " * 5 + "A"
        + "  відмінно\n"
        + "Історія" + " " * 15 + " " * 7 + "3" + " " * 4 + "74" + " " * 5 + "D"
        + "  добре\n"
        + "Бази даних" + " " * 12 + " " * 7 + "4" + " " * 4 + "50" + " " * 4 + "FX"
        + "  незадовільно\n"
        + "-" * 50 + "\n"
        + "Усього кредитів: 12\n"
        + "Середній бал (зважений за кредитами): 74,8\n"
        + "Борги: Бази даних\n"
    )
    assert transcript(student, "КН-41") == expected


def test_separator_width_is_w_and_appears_twice():
    assert W == 50
    result = transcript(make_student([Grade("Python", 90, D1)]))
    lines = result.splitlines()
    assert lines.count("-" * W) == 2
    assert lines[3] == "-" * W


def test_single_grade_summary_lines():
    result = transcript(make_student([Grade("Python", 95, D1)]))
    assert result.endswith(
        "-" * 50 + "\n"
        "Усього кредитів: 5\n"
        "Середній бал (зважений за кредитами): 95,0\n"
        "Боргів немає\n"
    )


# ---------------------------------------------------------------------------
# Шкали оцінювання: ECTS і національна (усі межі)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score, ects, national",
    [
        (100, "A", "відмінно"),
        (90, "A", "відмінно"),
        (89, "B", "добре"),
        (82, "B", "добре"),
        (81, "C", "добре"),
        (75, "C", "добре"),
        # Розбіжність шкал зі старої системи: ECTS "D", але національна "добре".
        (74, "D", "добре"),
        (73, "D", "задовільно"),
        (67, "D", "задовільно"),
        (66, "E", "задовільно"),
        (60, "E", "задовільно"),
        (59, "FX", "незадовільно"),
        (35, "FX", "незадовільно"),
        (34, "F", "незадовільно"),
        (0, "F", "незадовільно"),
    ],
)
def test_grade_scales_boundaries(score, ects, national):
    result = transcript(make_student([Grade("Python", score, D1)]))
    row = row_for(result, "Python")
    assert row["score"] == str(score)
    assert row["ects"] == ects
    assert row["national"] == "  " + national


@pytest.mark.parametrize("score", [59, 35, 34, 0])
def test_failing_score_creates_debt(score):
    result = transcript(make_student([Grade("Python", score, D1)]))
    assert "Борги: Python\n" in result
    assert "Боргів немає" not in result


@pytest.mark.parametrize("score", [60, 74, 90, 100])
def test_passing_score_has_no_debt(score):
    result = transcript(make_student([Grade("Python", score, D1)]))
    assert result.endswith("Боргів немає\n")
    assert "Борги:" not in result


# ---------------------------------------------------------------------------
# Кредити ЄКТС
# ---------------------------------------------------------------------------


def test_credits_table_constant():
    assert CREDITS == {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}


@pytest.mark.parametrize(
    "course, credits",
    [
        ("Python", 5),
        ("Бази даних", 4),
        ("Алгоритми", 5),
        ("Веброзробка", 4),
        # Дисципліна, якої немає в CREDITS, отримує 3 кредити за замовчуванням.
        ("Філософія", 3),
    ],
)
def test_credits_per_course(course, credits):
    result = transcript(make_student([Grade(course, 80, D1)]))
    assert row_for(result, course)["credits"] == str(credits)
    assert f"Усього кредитів: {credits}\n" in result


def test_total_credits_sum_over_distinct_courses():
    student = make_student(
        [
            Grade("Python", 80, D1),
            Grade("Python", 85, D2),  # повтор тієї ж дисципліни не додає кредитів
            Grade("Бази даних", 80, D1),
            Grade("Філософія", 80, D1),
        ]
    )
    assert "Усього кредитів: 12\n" in transcript(student)


# ---------------------------------------------------------------------------
# Сортування дисциплін і порядок боргів
# ---------------------------------------------------------------------------


def test_courses_sorted_by_unicode_code_points():
    student = make_student(
        [
            Grade("Веброзробка", 80, D1),
            Grade("Бази даних", 80, D1),
            Grade("Алгоритми", 80, D1),
            Grade("Історія", 80, D1),
            Grade("Python", 80, D1),
        ]
    )
    result = transcript(student)
    positions = [
        result.index(c.ljust(22))
        for c in ["Python", "Історія", "Алгоритми", "Бази даних", "Веброзробка"]
    ]
    assert positions == sorted(positions)


def test_debts_listed_in_sorted_course_order():
    student = make_student(
        [
            Grade("Бази даних", 40, D1),
            Grade("Python", 95, D1),
            Grade("Історія", 20, D1),
            Grade("Алгоритми", 59, D1),
        ]
    )
    result = transcript(student)
    assert "Борги: Історія, Алгоритми, Бази даних\n" in result


def test_each_course_appears_once_in_table():
    student = make_student(
        [
            Grade("Python", 50, D1),
            Grade("Python", 70, D2),
            Grade("Python", 90, D3),
        ]
    )
    result = transcript(student)
    assert sum(1 for ln in result.splitlines() if ln.startswith("Python")) == 1


# ---------------------------------------------------------------------------
# Вибір останньої оцінки з дисципліни (перескладання)
# ---------------------------------------------------------------------------


def test_latest_grade_by_date_wins_regardless_of_list_order():
    # Пізніша за датою оцінка стоїть у списку першою, тож пізніше в списку
    # трапляється раніша дата, і умова >= для неї не спрацьовує.
    student = make_student(
        [
            Grade("Python", 40, D2),
            Grade("Python", 85, D1),
        ]
    )
    result = transcript(student)
    row = row_for(result, "Python")
    assert row["score"] == "40"
    assert row["ects"] == "FX"
    assert "Борги: Python\n" in result


def test_successful_retake_clears_debt():
    student = make_student(
        [
            Grade("Python", 30, D1),
            Grade("Python", 75, D2),
        ]
    )
    result = transcript(student)
    row = row_for(result, "Python")
    assert row["score"] == "75"
    assert row["ects"] == "C"
    assert result.endswith("Боргів немає\n")


def test_same_date_later_in_list_wins():
    # Через ">=" з кількох оцінок з однаковою датою береться остання в списку.
    student = make_student(
        [
            Grade("Python", 50, D1),
            Grade("Python", 70, D1),
        ]
    )
    assert row_for(transcript(student), "Python")["score"] == "70"


def test_average_uses_only_latest_grade():
    student = make_student(
        [
            Grade("Python", 20, D1),
            Grade("Python", 100, D2),
        ]
    )
    assert "Середній бал (зважений за кредитами): 100,0\n" in transcript(student)


# ---------------------------------------------------------------------------
# Середній бал: зважування, округлення, формат
# ---------------------------------------------------------------------------


def test_weighted_average_by_credits():
    # (90*5 + 60*3) / 8 = 630 / 8 = 78.75, що дає 78,8
    student = make_student([Grade("Python", 90, D1), Grade("Філософія", 60, D1)])
    assert "Середній бал (зважений за кредитами): 78,8\n" in transcript(student)


def test_average_rounds_half_up_not_bankers():
    # (88*5 + 62*3) / 8 = 626 / 8 = 78.25. Округлення «половина вгору» дає 78,3,
    # а банківське дало б 78,2.
    student = make_student([Grade("Python", 88, D1), Grade("Філософія", 62, D1)])
    assert "Середній бал (зважений за кредитами): 78,3\n" in transcript(student)


def test_average_rounds_down_below_half():
    # (81 + 80 + 80) / 3 = 80.333..., що дає 80,3
    student = make_student(
        [
            Grade("Історія", 81, D1),
            Grade("Філософія", 80, D1),
            Grade("Соціологія", 80, D1),
        ]
    )
    assert "Середній бал (зважений за кредитами): 80,3\n" in transcript(student)


def test_average_uses_comma_as_decimal_separator():
    student = make_student([Grade("Python", 82, D1), Grade("Алгоритми", 83, D1)])
    result = transcript(student)
    line = [ln for ln in result.splitlines() if ln.startswith("Середній бал")][0]
    assert line == "Середній бал (зважений за кредитами): 82,5"
    assert "." not in line


def test_integer_average_keeps_trailing_zero():
    student = make_student([Grade("Python", 70, D1), Grade("Алгоритми", 80, D1)])
    assert "Середній бал (зважений за кредитами): 75,0\n" in transcript(student)


def test_failing_grades_still_count_in_average():
    # (100*4 + 0*4) / 8 = 50
    student = make_student([Grade("Бази даних", 100, D1), Grade("Веброзробка", 0, D1)])
    result = transcript(student)
    assert "Середній бал (зважений за кредитами): 50,0\n" in result
    assert "Борги: Веброзробка\n" in result


# ---------------------------------------------------------------------------
# Побічні ефекти
# ---------------------------------------------------------------------------


def test_does_not_mutate_student_grades():
    grades = [
        Grade("Бази даних", 50, D2),
        Grade("Python", 95, D1),
        Grade("Python", 60, D3),
    ]
    student = make_student(grades)
    snapshot = list(student.grades)
    transcript(student, "КН-41")
    assert student.grades == snapshot


def test_returns_str():
    assert isinstance(transcript(make_student()), str)
    assert isinstance(transcript(make_student([Grade("Python", 90, D1)])), str)
