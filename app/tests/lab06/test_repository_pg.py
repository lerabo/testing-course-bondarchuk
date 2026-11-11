"""Інтеграційні тести Р-22 на PostgreSQL у контейнері (техніки проєктування ЛР 3)."""

from datetime import date

import pytest

from student_portal.exceptions import DuplicateStudentError, StudentNotFoundError
from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.status import Status


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


def koval() -> Student:
    return Student(
        1,
        "Олена",
        "Коваль",
        [
            Grade("Python", 95, date(2026, 10, 1)),
            Grade("Бази даних", 88, date(2026, 10, 8)),
        ],
        "o.koval@students.example.edu",
        funding=Funding.CONTRACT,
        status=Status.ON_LEAVE,
    )


def last_names(students):
    return [s.last_name for s in students]


# ---------------------------------------------------------- create_schema


def test_create_schema_is_idempotent(repository):
    repository.create_schema()  # таблиці вже є - повторний виклик не падає
    repository.add(koval())
    assert repository.get(1) == koval()


# ---------------------------------------------------------- add / get


def test_added_student_is_returned_equal(repository):
    repository.add(koval())
    assert repository.get(1) == koval()


def test_student_without_grades_and_email(repository):
    student = Student(2, "Андрій", "Мельник")
    repository.add(student)
    assert repository.get(2) == student


def test_grades_are_returned_ordered_by_date(repository):
    student = Student(
        3,
        "Ірина",
        "Шевчук",
        [
            Grade("Бази даних", 70, date(2026, 10, 8)),
            Grade("Python", 82, date(2026, 10, 1)),
            Grade("Мережі", 60, date(2026, 9, 25)),
        ],
    )
    repository.add(student)
    loaded = repository.get(3)
    assert [g.graded_on for g in loaded.grades] == [
        date(2026, 9, 25),
        date(2026, 10, 1),
        date(2026, 10, 8),
    ]


def test_get_missing_student_raises(repository):
    with pytest.raises(StudentNotFoundError):
        repository.get(999)


@known_defect("#37")
def test_add_duplicate_id_raises(repository):
    repository.add(koval())
    with pytest.raises(DuplicateStudentError):
        repository.add(Student(1, "Дубль", "Дубль"))


@known_defect("#37")
def test_duplicate_keeps_data_and_repository_usable(repository):
    repository.add(koval())
    with pytest.raises(Exception):  # noqa: B017 - тип помилки перевіряє тест вище
        repository.add(Student(1, "Дубль", "Дубль"))
    assert repository.get(1) == koval()
    repository.add(Student(2, "Андрій", "Мельник"))
    assert repository.get(2).last_name == "Мельник"


# ---------------------------------------------------------- add_grade


def test_add_grade_appends_grade(repository):
    repository.add(koval())
    repository.add_grade(1, Grade("Мережі", 74, date(2026, 10, 15)))
    assert repository.get(1).grades[-1] == Grade("Мережі", 74, date(2026, 10, 15))


def test_add_grade_to_missing_student_raises_and_repository_stays_usable(repository):
    with pytest.raises(StudentNotFoundError):
        repository.add_grade(999, Grade("Python", 50))
    repository.add(koval())
    assert repository.get(1).last_name == "Коваль"


# ---------------------------------------------------------- find

GROUP = [
    ("Олена", "Коваль"),
    ("Ігор", "Коваленко"),
    ("Богдан", "Ткачук"),
    ("Анна", "Ткачук"),
    ("Марта", "Сто%ко"),
    ("Петро", "Під_крес"),
]


@pytest.fixture
def group_repository(repository):
    for student_id, (first, last) in enumerate(GROUP, start=1):
        repository.add(Student(student_id, first, last))
    return repository


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("Коваль", ["Коваль"], id="exact-case"),
        pytest.param("  Коваль  ", ["Коваль"], id="surrounding-spaces"),
        pytest.param("ова", ["Коваленко", "Коваль"], id="middle-of-name"),
        pytest.param("К", ["Коваленко", "Коваль"], id="one-letter"),
        pytest.param("Шевчук", [], id="no-match"),
        pytest.param("коваль", ["Коваль"], id="lowercase", marks=known_defect("#38")),
        pytest.param("КОВАЛЬ", ["Коваль"], id="uppercase", marks=known_defect("#38")),
        pytest.param("%", ["Сто%ко"], id="percent", marks=known_defect("#39")),
        pytest.param("_", ["Під_крес"], id="underscore", marks=known_defect("#39")),
    ],
)
def test_find(group_repository, query, expected):
    assert last_names(group_repository.find(query)) == expected


def test_empty_query_returns_everybody(group_repository):
    assert len(group_repository.find("")) == len(GROUP)


def test_same_last_names_ordered_by_first_name(group_repository):
    found = group_repository.find("Ткачук")
    assert [s.first_name for s in found] == ["Анна", "Богдан"]


@known_defect("#40")
def test_find_orders_by_ukrainian_alphabet(repository):
    alphabetical = [
        "Андрієнко",
        "Гнатюк",
        "Ґудзь",
        "Дмитренко",
        "Єрмак",
        "Іваненко",
        "Їжак",
    ]
    for student_id, last in enumerate(reversed(alphabetical), start=1):
        repository.add(Student(student_id, "Ім'я", last))
    assert last_names(repository.find("")) == alphabetical
