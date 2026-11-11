"""Р-20: тести send_debt_reminders і SmtpMailer з тестовими дублерами.

Справжні листи не надсилаються: поштовий сервер замінено фейком, mock-об'єктом
з автоспецифікацією або підміною класу SMTP через pytest-mock.
"""

from datetime import date
from unittest.mock import call, create_autospec

import pytest

from student_portal import reminders
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.reminders import (
    SUBJECT,
    Mailer,
    ReminderReport,
    SmtpMailer,
    send_debt_reminders,
)
from student_portal.status import Status

TODAY = date(2026, 1, 15)
DEADLINE = "14.02.2026"  # TODAY + 30 календарних днів


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


class FakeMailer:
    """Фейк: справжня, але спрощена реалізація протоколу Mailer."""

    def __init__(self):
        self.outbox: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append((to, subject, body))


def debtor(student_id=1, email="m@example.edu", status=Status.ACTIVE, scores=(45,)):
    grades = [Grade(f"Дисципліна {i}", s) for i, s in enumerate(scores)]
    return Student(student_id, "Максим", "Бондар", grades, email, status=status)


def group_of(*students: Student) -> Group:
    group = Group("КН-11")
    for student in students:
        group.add(student)
    return group


# ------------------------------------------------------------ фейк: стан


def test_debtor_gets_letter_with_subject_courses_and_deadline():
    # Arrange
    student = Student(
        1,
        "Максим",
        "Бондар",
        [Grade("Python", 45), Grade("Бази даних", 90)],
        "m@example.edu",
    )
    mailer = FakeMailer()
    # Act
    report = send_debt_reminders(group_of(student), mailer, today=TODAY)
    # Assert
    [(to, subject, body)] = mailer.outbox
    assert (to, subject) == ("m@example.edu", SUBJECT)
    assert "Python" in body
    assert "Бази даних" not in body
    assert DEADLINE in body
    assert report == ReminderReport(sent=["m@example.edu"], failed=[])


@known_defect("#29")
def test_debtor_with_several_debts_gets_one_letter():
    # Arrange
    student = Student(
        1,
        "Максим",
        "Бондар",
        [Grade("Python", 45), Grade("Бази даних", 50)],
        "m@example.edu",
    )
    mailer = FakeMailer()
    # Act
    send_debt_reminders(group_of(student), mailer, today=TODAY)
    # Assert
    [(_, _, body)] = mailer.outbox
    assert "Бази даних, Python" in body


def test_no_debtors_no_letters():
    mailer = FakeMailer()
    report = send_debt_reminders(group_of(debtor(scores=(90,))), mailer, today=TODAY)
    assert mailer.outbox == []
    assert report == ReminderReport()


# ------------------------------------------- mock з автоспецифікацією: взаємодія


def test_active_debtor_is_notified_once():
    # Arrange
    mailer = create_autospec(Mailer, instance=True)
    # Act
    send_debt_reminders(group_of(debtor()), mailer, today=TODAY)
    # Assert
    mailer.send.assert_called_once()
    to, subject, body = mailer.send.call_args.args
    assert (to, subject) == ("m@example.edu", SUBJECT)
    assert DEADLINE in body


@pytest.mark.parametrize(
    "student",
    [
        pytest.param(
            debtor(status=Status.ON_LEAVE), id="on-leave", marks=known_defect("#30")
        ),
        pytest.param(debtor(status=Status.EXPELLED), id="expelled"),
        pytest.param(
            debtor(status=Status.GRADUATED), id="graduated", marks=known_defect("#30")
        ),
        pytest.param(debtor(email=None), id="no-email"),
        pytest.param(debtor(scores=(60, 95)), id="no-fx"),
    ],
)
def test_reminder_not_sent(student):
    # Arrange
    mailer = create_autospec(Mailer, instance=True)
    # Act
    report = send_debt_reminders(group_of(student), mailer, today=TODAY)
    # Assert
    mailer.send.assert_not_called()
    assert report.sent == []


def test_autospec_rejects_wrong_call_signature():
    # Автоспецифікація перевіряє сигнатуру: виклик з неіснуючим аргументом падає,
    # а звичайний Mock() мовчки прийняв би будь-що.
    mailer = create_autospec(Mailer, instance=True)
    with pytest.raises(TypeError):
        mailer.send("m@example.edu", SUBJECT, "текст", cc="x@example.edu")


# ------------------------------------------------------ side_effect: імітація збою


@known_defect("#31")
def test_failed_letter_does_not_stop_mailing():
    # Arrange
    group = group_of(debtor(1, "a@example.edu"), debtor(2, "b@example.edu"))
    mailer = create_autospec(Mailer, instance=True)
    mailer.send.side_effect = [ConnectionError("smtp down"), None]
    # Act
    report = send_debt_reminders(group, mailer, today=TODAY)
    # Assert
    assert mailer.send.call_count == 2
    assert report == ReminderReport(sent=["b@example.edu"], failed=["a@example.edu"])


# ------------------------------------------------------ підміна SMTP (pytest-mock)


@pytest.fixture
def smtp(mocker):
    # Підміняємо ім'я там, де його шукає код: reminders.py робить
    # `from smtplib import SMTP`, тому патч "smtplib.SMTP" сюди не дістається.
    smtp_class = mocker.patch("student_portal.reminders.SMTP", autospec=True)
    return smtp_class.return_value.__enter__.return_value


def test_smtp_mailer_connects_with_starttls_and_login(smtp):
    # Arrange
    mailer = SmtpMailer(
        "smtp.vnu.example.edu",
        sender="dekanat@vnu.example.edu",
        username="dekanat",
        password="secret",  # noqa: S106 - тестове значення для підміненого SMTP
    )
    # Act
    mailer.send("m@example.edu", SUBJECT, "текст листа")
    # Assert
    reminders.SMTP.assert_called_once_with("smtp.vnu.example.edu", 587, timeout=10)
    assert smtp.method_calls[:2] == [call.starttls(), call.login("dekanat", "secret")]
    [message] = smtp.send_message.call_args.args
    assert message["From"] == "dekanat@vnu.example.edu"
    assert message["To"] == "m@example.edu"
    assert message["Subject"] == SUBJECT
    assert message.get_content().strip() == "текст листа"


def test_smtp_mailer_without_username_does_not_login(smtp):
    SmtpMailer("smtp.vnu.example.edu").send("m@example.edu", SUBJECT, "текст")
    smtp.starttls.assert_called_once()
    smtp.login.assert_not_called()
    smtp.send_message.assert_called_once()
