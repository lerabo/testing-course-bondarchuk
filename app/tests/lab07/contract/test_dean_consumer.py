"""Р-24, сторона споживача: сервіс деканату очікує від API картку студента."""

import shutil
from pathlib import Path

import pytest
from pact import Pact, match

from student_portal.dean_client import StudentCard, fetch_student_card

PACTS = Path(__file__).parent / "pacts"
AUTH = match.regex("Bearer admin-token", regex=r"Bearer .+")


@pytest.fixture(scope="module", autouse=True)
def fresh_pacts():
    """Контракт щоразу будується наново з усіх тестів модуля."""
    shutil.rmtree(PACTS, ignore_errors=True)


@pytest.fixture
def pact():
    pact = Pact("dean-office", "student-portal").with_specification("V4")
    yield pact
    pact.write_file(PACTS)  # додає взаємодію до наявного файла


def test_card_of_student_with_grades(pact):
    (
        pact.upon_receiving("запит картки студента з оцінками")
        .given("студент з id 1 має оцінки")
        .with_request("GET", "/api/students/1")
        .with_header("Authorization", AUTH)
        .will_respond_with(200)
        .with_body(
            {
                "first_name": match.str("Олена"),
                "last_name": match.str("Коваль"),
                "email": match.str("o.koval@students.example.edu"),
                "group": match.str("КН-11"),
                "average": match.number(92.5),
                "funding": match.regex(
                    "державне замовлення", regex="державне замовлення|контракт"
                ),
            }
        )
    )
    with pact.serve() as server:
        card = fetch_student_card(str(server.url), "admin-token", 1)

    assert card == StudentCard(
        full_name="Коваль Олена",
        email="o.koval@students.example.edu",
        group="КН-11",
        average="92.5",
        budget=True,
    )


def test_card_of_student_without_grades(pact):
    (
        pact.upon_receiving("запит картки студента без оцінок")
        .given("студент з id 5 не має оцінок")
        .with_request("GET", "/api/students/5")
        .with_header("Authorization", AUTH)
        .will_respond_with(200)
        .with_body(
            {
                "first_name": match.str("Софія"),
                "last_name": match.str("Ткачук"),
                "email": match.str("s.tkachuk@students.example.edu"),
                "group": match.str("КН-11"),
                "average": None,
                "funding": match.regex(
                    "державне замовлення", regex="державне замовлення|контракт"
                ),
            }
        )
    )
    with pact.serve() as server:
        card = fetch_student_card(str(server.url), "admin-token", 5)

    assert card == StudentCard(
        full_name="Ткачук Софія",
        email="s.tkachuk@students.example.edu",
        group="КН-11",
        average="-",
        budget=True,
    )
