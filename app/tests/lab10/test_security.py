"""Тести безпеки Р-27 (експорт, імпорт, доступ) і НФ-безпеки (режим налагодження)."""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from student_portal.api import create_app
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

ADMIN = {"Authorization": "Bearer admin-token"}
TEACHER = {"Authorization": "Bearer teacher-token"}
HEADER = "last_name;first_name;email;funding\n"
# Ознаки технічних подробиць у відповіді: трасування, шляхи, фрагменти коду
INTERNALS = ("Traceback", 'File "', ".py", "site-packages", "Error:")


def known_defect(issue: str):
    # raises: тест має падати саме на перевірці, а не на сторонньому винятку
    return pytest.mark.xfail(
        strict=True, raises=AssertionError, reason=f"відомий дефект {issue}"
    )


def make_group(*students: Student) -> Group:
    group = Group("КН-11")
    for s in students or (
        Student(1, "Олена", "Коваль", [Grade("Python", 95)], email="o@ex.edu"),
    ):
        group.add(s)
    return group


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("PORTAL_DEBUG", raising=False)
    # 500 - відповідь, а не виняток у тесті: так її побачить клієнт
    return TestClient(create_app(make_group()), raise_server_exceptions=False)


def upload(client, content: bytes, headers=ADMIN):
    files = {"file": ("students.csv", content, "text/csv")}
    return client.post("/api/students/import", files=files, headers=headers)


def exported_rows(client) -> list[dict[str, str]]:
    response = client.get("/api/export/students.csv", headers=TEACHER)
    assert response.status_code == 200
    text = response.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline=""), delimiter=";"))


# --- Захист від формул (OWASP CSV Injection) ---------------------------------
# Клас еквівалентності на кожен небезпечний символ зі специфікації і на кожне
# текстове поле, що потрапляє в CSV.

FORMULA_STARTS = {
    "=": "=1+1",
    "+": "+1+1",
    "-": "-1+1",
    "@": "@SUM(A1:A2)",
    "tab": "\t=1+1",
    "cr": "\r=1+1",
}
# Email проходить перевірку EmailStr, тож у ньому можливі лише =, + і - на початку
EMAIL_FORMULAS = {"=": "=1+1@ex.edu", "+": "+1@ex.edu", "-": "-1@ex.edu"}
FORMULA_CASES = [
    pytest.param(field, value, id=f"{char}-{field}")
    for field in ("last_name", "first_name")
    for char, value in FORMULA_STARTS.items()
] + [
    pytest.param("email", value, id=f"{char}-email")
    for char, value in EMAIL_FORMULAS.items()
]
SAFE_CASES = [
    pytest.param(field, value, id=f"{name}-{field}")
    for field in ("last_name", "first_name")
    for name, value in [
        ("plain", "Коваль"),
        ("inner-equals", "Ко=валь"),
        ("apostrophe", "О'Коннор"),
        ("inner-hyphen", "Мельник-Шевченко"),
    ]
] + [
    pytest.param("email", value, id=f"{name}-email")
    for name, value in [
        ("plain", "o@ex.edu"),
        ("inner-equals", "o=1@ex.edu"),
        ("inner-hyphen", "o-k@ex.edu"),
        ("inner-plus", "a+b@ex.edu"),
    ]
]


def student_with(field: str, value: str) -> Student:
    data = {"first_name": "Олена", "last_name": "Коваль", "email": "o@ex.edu"}
    data[field] = value
    return Student(
        1,
        data["first_name"],
        data["last_name"],
        [Grade("Python", 95)],
        email=data["email"],
    )


@pytest.mark.parametrize(("field", "value"), FORMULA_CASES)
@known_defect("#77")
def test_formula_is_exported_with_apostrophe(monkeypatch, field, value):
    monkeypatch.delenv("PORTAL_DEBUG", raising=False)
    client = TestClient(create_app(make_group(student_with(field, value))))

    [row] = exported_rows(client)

    assert row[field] == "'" + value


@pytest.mark.parametrize(("field", "value"), SAFE_CASES)
def test_value_without_formula_is_unchanged(monkeypatch, field, value):
    monkeypatch.delenv("PORTAL_DEBUG", raising=False)
    client = TestClient(create_app(make_group(student_with(field, value))))

    [row] = exported_rows(client)

    assert row[field] == value


def test_export_is_attachment(client):
    response = client.get("/api/export/students.csv", headers=TEACHER)

    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == (
        'attachment; filename="students.csv"'
    )


# --- Імпорт: кодування, формат, порожній файл ---------------------------------


def test_utf8_file_is_imported(client):
    body = (HEADER + "Шевченко;Тарас;t@ex.edu;бюджет\n").encode("utf-8")

    response = upload(client, body)

    assert response.status_code == 201
    assert response.json() == {"imported": 1}


@pytest.mark.parametrize("encoding", ["cp1251", "utf-16"])
@known_defect("#78")
def test_file_in_other_encoding_is_400(client, encoding):
    body = (HEADER + "Шевченко;Тарас;t@ex.edu;бюджет\n").encode(encoding)

    response = upload(client, body)

    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


@known_defect("#76")
def test_server_error_reveals_no_internals(client):
    # Файл Windows-1251 зараз дає 500; відповідь не має розкривати код сервера
    body = (HEADER + "Шевченко;Тарас;t@ex.edu;бюджет\n").encode("cp1251")

    response = upload(client, body)

    assert not any(marker in response.text for marker in INTERNALS)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"last_name,first_name,email,funding\n",
        b"last_name;first_name;email\n",
        (HEADER + "Шевченко;Тарас;;бюджет\n").encode(),
        (HEADER + "Шевченко;Тарас;t@ex.edu;грант\n").encode(),
        (HEADER + "Коваль;Олена;o@ex.edu;бюджет\n").encode(),
    ],
    ids=[
        "empty",
        "comma-separated",
        "missing-column",
        "no-email",
        "bad-funding",
        "duplicate-email",
    ],
)
def test_wrong_format_is_400_without_internals(client, body):
    response = upload(client, body)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail
    assert not any(marker in detail for marker in INTERNALS)


@known_defect("#79")
def test_invalid_email_is_rejected_and_list_still_works(client):
    body = (HEADER + "Шевченко;Тарас;не-email;бюджет\n").encode()

    response = upload(client, body)

    assert response.status_code == 400
    assert client.get("/api/students", headers=TEACHER).status_code == 200
    assert client.get("/api/export/students.csv", headers=TEACHER).status_code == 200


# --- НФ-безпека: режим налагодження --------------------------------------------


@known_defect("#76")
def test_debug_is_off_by_default(monkeypatch):
    monkeypatch.delenv("PORTAL_DEBUG", raising=False)

    assert create_app(make_group()).debug is False


@pytest.mark.parametrize(("value", "expected"), [("1", True), ("0", False)])
def test_debug_follows_variable(monkeypatch, value, expected):
    monkeypatch.setenv("PORTAL_DEBUG", value)

    assert create_app(make_group()).debug is expected


def test_server_error_without_debug_is_generic(monkeypatch):
    monkeypatch.setenv("PORTAL_DEBUG", "0")
    client = TestClient(create_app(make_group()), raise_server_exceptions=False)
    body = (HEADER + "Шевченко;Тарас;t@ex.edu;бюджет\n").encode("cp1251")

    response = upload(client, body)

    assert response.status_code == 500
    assert response.text == "Internal Server Error"


# --- Доступ: матриця ролей ЛР 7 ------------------------------------------------

ROLE_HEADERS = {
    "admin": ADMIN,
    "teacher": TEACHER,
    "student": {"Authorization": "Bearer student-1-token"},
    "unknown-token": {"Authorization": "Bearer forged-token"},
    "anonymous": {},
}


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("admin", 201),
        ("teacher", 403),
        ("student", 403),
        ("unknown-token", 401),
        ("anonymous", 401),
    ],
)
def test_import_access(client, role, expected):
    body = (HEADER + "Шевченко;Тарас;t@ex.edu;бюджет\n").encode()

    response = upload(client, body, headers=ROLE_HEADERS[role])

    assert response.status_code == expected


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("admin", 200),
        ("teacher", 200),
        ("student", 403),
        ("unknown-token", 401),
        ("anonymous", 401),
    ],
)
def test_export_access(client, role, expected):
    response = client.get("/api/export/students.csv", headers=ROLE_HEADERS[role])

    assert response.status_code == expected
    if expected != 200:
        assert "Коваль" not in response.text
