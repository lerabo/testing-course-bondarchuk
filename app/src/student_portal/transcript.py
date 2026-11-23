"""Академічна довідка студента (вимога Р-28).

Перенесено з системи деканату попередньої версії (2019). ЛР 11: рефакторинг під
захистом характеризаційних тестів, потім виправлення за Р-28 (#92, #93).
"""

from student_portal.grades import Grade
from student_portal.people import Funding, Student

# кредити ЄКТС; інші дисципліни - 3 кредити
CREDITS = {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}
DEFAULT_CREDITS = 3
RULE = "-" * 50

FAIL = "незадовільно"
# національна шкала - за літерою ECTS (Р-28): B і C - «добре», D і E - «задовільно»
NATIONAL = {
    "A": "відмінно",
    "B": "добре",
    "C": "добре",
    "D": "задовільно",
    "E": "задовільно",
    "Fx": FAIL,
}


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
        letter = grade.ects  # шкала Р-05: Fx для 0–59 (#92)
        word = NATIONAL[letter]  # за літерою, а не за балом (#93)
        if word == FAIL:
            debts.append(course)
        weighted_total += grade.score * credits
        total_credits += credits
        lines.append(row(course, credits, grade.score, letter, word))
    lines.append(RULE)
    lines += summary(total_credits, weighted_total, debts)
    return "\n".join(lines) + "\n"
