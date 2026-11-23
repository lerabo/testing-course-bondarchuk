"""Академічна довідка студента (вимога Р-28).

Перенесено з системи деканату попередньої версії (2019) майже без змін.
"""

from student_portal.people import Funding

# кредити ЄКТС; інші дисципліни - 3 кредити
CREDITS = {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}
W = 50
# шкала старої системи: нижня межа балу і літера; перша відповідна межа
ECTS_SCALE = [
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
NATIONAL_SCALE = [(90, "відмінно"), (74, "добре"), (60, "задовільно"), (0, FAIL)]


def by_threshold(scale, score):
    # нижче за найменшу межу - останнє значення шкали, як else у старому коді
    return next((value for lower, value in scale if score >= lower), scale[-1][1])


def title(student, group_name=""):
    s = ""
    s = s + "АКАДЕМІЧНА ДОВІДКА\n"
    s = s + "Студент: " + student.last_name + " " + student.first_name
    s = s + " (id " + str(student.id) + ")"
    if group_name != "":
        s = s + ", група " + group_name
    s = s + "\n"
    f = "контракт"
    if student.funding == Funding.BUDGET:
        f = "державне замовлення"
    s = s + "Форма навчання: " + f + "\n"
    return s


def row(course, credits, score, letter, word):
    """Рядок таблиці: назва 22 ліворуч, кредити 8, бали 6, літера 6 праворуч."""
    return f"{course:<22}{credits:>8}{score:>6}{letter:>6}  {word}\n"


def final_grades(student):
    """Пари (дисципліна, зарахована оцінка) у порядку назв дисциплін."""
    courses = []
    for g in student.grades:
        if g.course not in courses:
            courses.append(g.course)
    courses.sort()
    result = []
    for c in courses:
        # зараховується остання оцінка з дисципліни
        last = None
        for g in student.grades:
            if g.course == c and (last is None or g.graded_on >= last.graded_on):
                last = g
        result.append((c, last))
    return result


def transcript(student, group_name=""):  # noqa: C901 - технічний борг, див. Р-28
    s = title(student, group_name)
    if len(student.grades) == 0:
        s = s + "Оцінок немає\n"
        return s
    s = s + "-" * W + "\n"
    s = s + row("Дисципліна", "Кредити", "Бали", "ECTS", "Оцінка")
    total = 0
    cr = 0
    debts = []
    for c, last in final_grades(student):
        k = CREDITS.get(c, 3)
        p = last.score
        e = by_threshold(ECTS_SCALE, p)
        n = by_threshold(NATIONAL_SCALE, p)
        if n == FAIL:
            debts.append(c)
        total = total + p * k
        cr = cr + k
        s = s + row(c, k, p, e, n)
    s = s + "-" * W + "\n"
    s = s + "Усього кредитів: " + str(cr) + "\n"
    avg = int(total / cr * 10 + 0.5) / 10
    s = s + "Середній бал (зважений за кредитами): " + str(avg).replace(".", ",")
    s = s + "\n"
    if len(debts) > 0:
        s = s + "Борги: " + ", ".join(debts) + "\n"
    else:
        s = s + "Боргів немає\n"
    return s
