"""Р-23: ресурс /api/students (схема, кругова перевірка, класи й межі, email)."""

import pytest
from api_schemas import STUDENT_SCHEMA, unique_student
from jsonschema import FormatChecker, validate

FORMATS = FormatChecker()


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


def assert_student(body):
    validate(body, STUDENT_SCHEMA, format_checker=FORMATS)


# ------------------------------------------------------------ схема і дані


def test_list_matches_schema_and_data(admin):
    response = admin.get("/api/students")
    assert response.status_code == 200
    students = response.json()
    for body in students:
        assert_student(body)
    koval = next(s for s in students if s["id"] == 1)
    assert (koval["last_name"], koval["average"]) == ("Коваль", 92.5)


def test_group_filter_keeps_only_that_group(admin):
    response = admin.get("/api/students", params={"group": "КН-11"})
    assert response.status_code == 200
    assert response.json()
    assert {s["group"] for s in response.json()} == {"КН-11"}


def test_unknown_group_gives_empty_list(admin):
    response = admin.get("/api/students", params={"group": "ПМ-99"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_student_matches_schema(admin):
    response = admin.get("/api/students/1")
    assert response.status_code == 200
    assert_student(response.json())
    assert response.json()["email"] == "o.koval@students.example.edu"


# ------------------------------------------------------------ створення


def test_create_returns_location_and_reads_back(admin, new_student):
    response = admin.post("/api/students", json=new_student)
    assert response.status_code == 201
    body = response.json()
    assert_student(body)
    assert response.headers["Location"] == f"/api/students/{body['id']}"
    assert body["average"] is None
    assert {k: body[k] for k in new_student} == new_student
    assert admin.get(response.headers["Location"]).json() == body


def test_unknown_fields_are_ignored(admin, new_student):
    response = admin.post("/api/students", json={**new_student, "role": "admin"})
    assert response.status_code == 201
    assert "role" not in response.json()


@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize(
    ("length", "expected"),
    [
        pytest.param(0, 422, id="len-0"),
        pytest.param(1, 201, id="len-1"),
        pytest.param(50, 201, id="len-50"),
        pytest.param(51, 422, id="len-51"),
    ],
)
def test_name_length(admin, new_student, field, length, expected):
    response = admin.post("/api/students", json={**new_student, field: "Я" * length})
    assert response.status_code == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("email", "not-an-email", id="email-invalid"),
        pytest.param("email", None, id="email-null"),
        pytest.param("first_name", None, id="first-name-null"),
        pytest.param("last_name", None, id="last-name-null"),
    ],
)
def test_invalid_value_rejected(admin, new_student, field, value):
    response = admin.post("/api/students", json={**new_student, field: value})
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["first_name", "last_name", "email"])
def test_missing_field_rejected(admin, new_student, field):
    body = {k: v for k, v in new_student.items() if k != field}
    assert admin.post("/api/students", json=body).status_code == 422


# ------------------------------------------------------------ унікальність email


def test_create_with_existing_email_in_other_case_conflicts(admin, new_student):
    body = {**new_student, "email": "O.KOVAL@students.example.edu"}
    assert admin.post("/api/students", json=body).status_code == 409


def test_update_to_other_students_email_conflicts(admin, created, new_student):
    location, _ = created
    body = {**new_student, "email": "O.Koval@Students.Example.Edu"}
    assert admin.put(location, json=body).status_code == 409


def test_update_keeps_own_email(admin, created):
    location, body = created
    data = {
        "first_name": "Тарасик",
        "last_name": body["last_name"],
        "email": body["email"],
    }
    response = admin.put(location, json=data)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Тарасик"


# ------------------------------------------------------------ зміна і видалення


def test_update_is_visible_in_next_get(admin, created):
    location, _ = created
    data = unique_student() | {"last_name": "Петренко"}
    response = admin.put(location, json=data)
    assert response.status_code == 200
    assert_student(response.json())
    assert admin.get(location).json()["last_name"] == "Петренко"


def test_update_with_invalid_body_rejected(admin, created):
    location, body = created
    data = {"first_name": "", "last_name": body["last_name"], "email": body["email"]}
    assert admin.put(location, json=data).status_code == 422


def test_update_missing_student_is_404(admin, new_student):
    assert admin.put("/api/students/99999", json=new_student).status_code == 404


def test_delete_then_get_is_404(admin, created):
    location, _ = created
    response = admin.delete(location)
    assert response.status_code == 204
    assert response.content == b""
    assert admin.get(location).status_code == 404


def test_delete_missing_student_is_404(admin):
    assert admin.delete("/api/students/99999").status_code == 404


def test_get_missing_student_is_404(admin):
    assert admin.get("/api/students/99999").status_code == 404
