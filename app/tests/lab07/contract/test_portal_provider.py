"""Р-24, сторона провайдера: API виконує контракт сервісу деканату."""

from pathlib import Path

from pact import Verifier

PACTS = Path(__file__).parent / "pacts"


def test_student_portal_honours_dean_contract(base_url):
    verifier = (
        Verifier("student-portal", host="127.0.0.1")
        .add_transport(url=base_url)
        .add_source(PACTS)
        .state_handler(
            {
                # Дані вже є в data/group.json, тож обробники нічого не готують.
                "студент з id 1 має оцінки": lambda action, parameters: None,
                "студент з id 5 не має оцінок": lambda action, parameters: None,
            }
        )
    )
    verifier.verify()
