"""Р-25: E2E-сценарії вебінтерфейсу для адміністратора, викладача і студента."""

import re

import pytest
from playwright.sync_api import expect

from .conftest import login_as
from .pages.login_page import LoginPage
from .pages.student_card import StudentCard
from .pages.students_page import StudentsPage

# ------------------------------------------------------------------ вхід і вихід


@pytest.mark.parametrize(
    ("token", "role"),
    [
        ("admin-token", "Адміністратор"),
        ("teacher-token", "Викладач"),
        ("student-1-token", "Студент"),
    ],
)
def test_login_shows_role_and_logout_returns_to_form(page, base_url, token, role):
    login = LoginPage(page, base_url).open().login(token)
    expect(login.role).to_have_text(role)
    login.logout.click()
    expect(login.token).to_be_visible()
    expect(login.logout).to_be_hidden()


def test_unknown_token_shows_alert_and_keeps_form(page, base_url):
    login = LoginPage(page, base_url).open().login("guest-token")
    expect(login.error).to_have_text("Невідомий токен")
    expect(login.token).to_be_visible()


# ------------------------------------------------------------ що бачить кожна роль


def test_admin_sees_add_form_and_delete_buttons(as_admin):
    expect(as_admin.add_form).to_be_visible()
    expect(as_admin.row_for("Коваль Олена").get_by_role("button")).to_have_text(
        "Видалити"
    )


def test_teacher_sees_list_without_add_form_and_delete(as_teacher):
    expect(as_teacher.row_for("Коваль Олена")).to_be_visible()
    expect(as_teacher.add_form).to_be_hidden()
    expect(as_teacher.delete_buttons).to_have_count(0)


def test_student_sees_only_own_card(page, base_url):
    LoginPage(page, base_url).open().login("student-1-token")
    card = StudentCard(page).wait_loaded()
    expect(card.name).to_have_text("Коваль Олена")
    expect(card.back).to_be_hidden()
    expect(card.grade_form).to_be_hidden()
    expect(StudentsPage(page).heading).to_be_hidden()


def test_teacher_sees_grade_form_admin_does_not(page, base_url):
    card = login_as(page, base_url, "teacher-token").open_card("Коваль Олена")
    expect(card.grade_form).to_be_visible()
    LoginPage(page, base_url).logout.click()
    card = login_as(page, base_url, "admin-token").open_card("Коваль Олена")
    expect(card.grade_form).to_be_hidden()


# ------------------------------------------------------------ значення в таблиці


def test_table_shows_name_email_and_total(as_admin, api):
    expect(as_admin.heading).to_be_visible()
    expect(as_admin.email_of("Коваль Олена")).to_have_text(
        "o.koval@students.example.edu"
    )
    expect(as_admin.total).to_have_text(
        f"Усього: {len(api.get('/api/students').json())}"
    )


@pytest.mark.parametrize(
    ("student", "average"),
    [
        pytest.param("Коваль Олена", "92,5", id="koval-92-5"),
        pytest.param("Шевчук Ірина", "82,0", id="shevchuk-82-0"),
        pytest.param("Ткачук Софія", "-", id="tkachuk-no-grades"),
    ],
)
def test_table_average_has_one_decimal(as_admin, student, average):
    expect(as_admin.average_of(student)).to_have_text(average)


def test_card_shows_average_and_grades(as_admin):
    card = as_admin.open_card("Коваль Олена")
    expect(card.name).to_have_text("Коваль Олена")
    expect(card.average).to_have_text("92,5")
    expect(card.grades).to_have_count(2)
    expect(card.grade_row("Python").locator("td")).to_have_text(
        ["Python", "95", "A", "2026-10-01"]
    )
    expect(card.grade_row("Бази даних").locator("td")).to_have_text(
        ["Бази даних", "90", "A", "2026-10-08"]
    )


# ------------------------------------------------------------------ пошук


def test_search_by_part_of_last_name(as_admin):
    as_admin.search_for("Кова")
    expect(as_admin.rows).to_have_count(1)
    expect(as_admin.row_for("Коваль Олена")).to_be_visible()


def test_search_ignores_case(as_admin):
    as_admin.search_for("коваль")
    expect(as_admin.rows).to_have_count(1)
    expect(as_admin.row_for("Коваль Олена")).to_be_visible()


def test_search_without_results(as_admin):
    as_admin.search_for("Шевченко")
    expect(as_admin.empty).to_be_visible()
    expect(as_admin.rows).to_have_count(0)


# ------------------------------------------------------------------ додавання


def test_add_student(as_admin, unique_email):
    before = int(as_admin.total.text_content().split()[-1])  # список уже завантажено
    as_admin.add_student("Гнатюк", "Тарас", unique_email)
    expect(as_admin.message).to_have_text("Студента додано: Гнатюк Тарас")
    expect(as_admin.row_for(unique_email)).to_be_visible()
    expect(as_admin.last_name).to_have_value("")
    expect(as_admin.email).to_have_value("")
    expect(as_admin.total).to_have_text(f"Усього: {before + 1}")


def test_add_with_used_email_keeps_entered_data(as_admin):
    as_admin.add_student("Дубльована", "Олена", "O.KOVAL@students.example.edu")
    expect(as_admin.error).to_have_text("Помилка: email уже використовується")
    expect(as_admin.last_name).to_have_value("Дубльована")
    expect(as_admin.email).to_have_value("O.KOVAL@students.example.edu")


def test_add_with_invalid_data_keeps_entered_data(as_admin, unique_email):
    too_long = "Я" * 51
    as_admin.add_student(too_long, "Олена", unique_email)
    expect(as_admin.error).to_have_text("Помилка: перевірте поля форми")
    expect(as_admin.last_name).to_have_value(too_long)


def test_used_email_does_not_add_row(as_admin):
    as_admin.add_student("Дубльований", "Тарас", "o.koval@STUDENTS.example.edu")
    expect(as_admin.error).to_have_text("Помилка: email уже використовується")
    expect(as_admin.row_for("Дубльований")).to_have_count(0)


# ------------------------------------------------------------------ видалення


def test_delete_after_confirmation(page, base_url, new_student, api):
    student_id, name = new_student
    students = login_as(page, base_url, "admin-token")
    before = int(students.total.text_content().split()[-1])
    dialog = students.delete(name, accept=True)
    expect(students.message).to_have_text("Студента видалено")
    expect(students.row_for(name)).to_have_count(0)
    assert dialog == [f"Видалити студента {name}?"]
    assert api.get(f"/api/students/{student_id}").status_code == 404
    expect(students.total).to_have_text(f"Усього: {before - 1}")


def test_cancel_delete_changes_nothing(page, base_url, new_student, api):
    student_id, name = new_student
    students = login_as(page, base_url, "admin-token")
    sent = []
    page.on("request", lambda r: sent.append((r.method, r.url)))
    students.delete(name, accept=False)
    # Позитивна ознака: наступна дія користувача (відкрити картку) вже відбулася,
    # отже запит на видалення, якби його надіслали, був би в списку раніше.
    with page.expect_request(re.compile(r".*/api/students/1/grades$")):
        students.open_card("Коваль Олена")
    assert [m for m, _ in sent if m == "DELETE"] == []
    assert api.get(f"/api/students/{student_id}").status_code == 200


# --------------------------------------------------------- картка і нова оцінка


def test_teacher_adds_grade_on_card(as_teacher, new_student):
    _, name = new_student
    card = as_teacher.open_card(name)
    card.add_grade("Python", 80)
    expect(card.message).to_have_text("Оцінку виставлено")
    expect(card.grade_row("Python").locator("td").nth(2)).to_have_text("C")
    expect(card.average).to_have_text("80,0")


def test_teacher_score_zero_is_accepted(as_teacher, new_student):
    _, name = new_student
    card = as_teacher.open_card(name)
    card.add_grade("Python", 0)
    expect(card.message).to_have_text("Оцінку виставлено")
    expect(card.grade_row("Python").locator("td").nth(2)).to_have_text("Fx")


@pytest.mark.parametrize("score", [-1, 101])
def test_teacher_score_out_of_range_shows_error(as_teacher, new_student, score):
    _, name = new_student
    card = as_teacher.open_card(name)
    card.add_grade("Python", score)
    expect(card.error).to_have_text("Помилка: бали від 0 до 100")
    expect(card.grades).to_have_count(0)


def test_list_after_card_shows_current_average(as_teacher, new_student):
    _, name = new_student
    card = as_teacher.open_card(name)
    card.add_grade("Python", 80)
    expect(card.message).to_have_text("Оцінку виставлено")
    card.back.click()
    expect(as_teacher.average_of(name)).to_have_text(re.compile(r"^80"))
