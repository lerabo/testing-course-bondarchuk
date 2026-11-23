"""Академічна довідка студента (вимога Р-28).

Перенесено з системи деканату попередньої версії (2019); ЛР 11 - рефакторинг
під захистом характеризаційних тестів, поведінку не змінено.
"""

from student_portal.grades import Grade
from student_portal.people import Funding, Student

# кредити ЄКТС; інші дисципліни - 3 кредити
CREDITS = {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}
DEFAULT_CREDITS = 3
RULE = "-" * 50

type Scale = list[tuple[int, str]]

# шкала старої системи: нижня межа балу і літера; перша відповідна межа
ECTS_SCALE: Scale = [
    (90, "A"),
    (82, "B"),
    (75, "C"),
    (67, "D"),
    (60, "E"),
    (35, "FX"),
    (0, "F"),
]

FAIL = "незадовільно"
# національна шкала старої системи - за балом, а не за літерою ECTS
NATIONAL_SCALE: Scale = [(90, "відмінно"), (74, "добре"), (60, "задовільно"), (0, FAIL)]


def by_threshold(scale: Scale, score: int) -> str:
    # нижче за найменшу межу - останнє значення шкали, як else у старому коді
    return next((value for lower, value in scale if score >= lower), scale[-1][1])


def title(student: Student, group_name: str = "") -> list[str]:
    group = f", група {group_name}" if group_name != "" else ""
    funding = "державне замовлення" if student.funding == Funding.BUDGET else "контракт"
    return [
        "АКАДЕМІЧНА ДОВІДКА",
        f"Студент: {student.last_name} {student.first_name} (id {student.id}){group}",
        f"Форма навчання: {funding}",
    ]


def row(
    course: str, credits: int | str, score: int | str, letter: str, word: str
) -> str:
    """Рядок таблиці: назва 22 ліворуч, кредити 8, бали 6, літера 6 праворуч."""
    return f"{course:<22}{credits:>8}{score:>6}{letter:>6}  {word}"


def final_grades(student: Student) -> list[tuple[str, Grade]]:
    """Пари (дисципліна, зарахована оцінка) у порядку назв дисциплін."""
    last: dict[str, Grade] = {}
    for grade in student.grades:
        # остання за датою; з однаковою датою - додана пізніше (>=)
        current = last.get(grade.course)
        if current is None or grade.graded_on >= current.graded_on:
            last[grade.course] = grade
    return sorted(last.items())


def half_up(value: float) -> float:
    """Округлення до десятих «половина вгору»; round() округлює 90,25 до 90,2."""
    return int(value * 10 + 0.5) / 10


def summary(credits: int, weighted_total: int, debts: list[str]) -> list[str]:
    average = str(half_up(weighted_total / credits)).replace(".", ",")
    return [
        f"Усього кредитів: {credits}",
        f"Середній бал (зважений за кредитами): {average}",
        f"Борги: {', '.join(debts)}" if debts else "Боргів немає",
    ]


def transcript(student: Student, group_name: str = "") -> str:
    lines = title(student, group_name)
    if not student.grades:
        lines.append("Оцінок немає")
        return "\n".join(lines) + "\n"
    lines += [RULE, row("Дисципліна", "Кредити", "Бали", "ECTS", "Оцінка")]
    weighted_total = 0
    total_credits = 0
    debts = []
    for course, grade in final_grades(student):
        credits = CREDITS.get(course, DEFAULT_CREDITS)
        word = by_threshold(NATIONAL_SCALE, grade.score)
        if word == FAIL:
            debts.append(course)
        weighted_total += grade.score * credits
        total_credits += credits
        letter = by_threshold(ECTS_SCALE, grade.score)
        lines.append(row(course, credits, grade.score, letter, word))
    lines.append(RULE)
    lines += summary(total_credits, weighted_total, debts)
    return "\n".join(lines) + "\n"
