"""Р-23: контроль доступу - таблиця «роль × запит → очікуваний код».

Шлях з {new} підставляється студентом, створеним у тесті, тож запити, що змінюють
дані, не зачіпають студентів з data/group.json навіть за зламаного контролю доступу.
"""

import pytest
from api_schemas import unique_student
from conftest import client_for

ADMIN, TEACHER, STUDENT_1 = "admin-token", "teacher-token", "student-1-token"
NEW_BODY = "NEW_STUDENT"  # тіло з унікальним email
GRADE_BODY = "GRADE"  # оцінка для студента {new}

REQUESTS = {
    "list": ("GET", "/api/students", None),
    "create": ("POST", "/api/students", NEW_BODY),
    "get-new": ("GET", "/api/students/{new}", None),
    "update-new": ("PUT", "/api/students/{new}", NEW_BODY),
    "delete-new": ("DELETE", "/api/students/{new}", None),
    "grade-new": ("POST", "/api/grades", GRADE_BODY),
    "grades-new": ("GET", "/api/students/{new}/grades", None),
}

# Очікувані коди за таблицею Р-23 і порядком перевірок 401 → 403 → 404.
EXPECTED = {
    None: dict.fromkeys(REQUESTS, 401),
    "unknown-token": dict.fromkeys(REQUESTS, 401),
    ADMIN: {
        "list": 200,
        "create": 201,
        "get-new": 200,
        "update-new": 200,
        "delete-new": 204,
        "grade-new": 403,
        "grades-new": 200,
    },
    TEACHER: {
        "list": 200,
        "create": 403,
        "get-new": 200,
        "update-new": 403,
        "delete-new": 403,
        "grade-new": 201,
        "grades-new": 200,
    },
    # студент 1 до чужого (щойно створеного) студента: BOLA / IDOR
    STUDENT_1: {
        "list": 403,
        "create": 403,
        "get-new": 403,
        "update-new": 403,
        "delete-new": 403,
        "grade-new": 403,
        "grades-new": 403,
    },
}

KNOWN = {}  # (token, request) -> issue; заповнюється за результатами запуску

MATRIX = [
    pytest.param(
        token,
        name,
        code,
        id=f"{token or 'no-token'}-{name}-{code}",
        marks=(
            [
                pytest.mark.xfail(
                    strict=True, reason=f"відомий дефект {KNOWN[token, name]}"
                )
            ]
            if (token, name) in KNOWN
            else []
        ),
    )
    for token, row in EXPECTED.items()
    for name, code in row.items()
]


@pytest.fixture
def new_id(admin):
    response = admin.post("/api/students", json=unique_student())
    return response.json()["id"]


@pytest.mark.parametrize(("token", "request_name", "expected"), MATRIX)
def test_access_control(base_url, admin, new_id, token, request_name, expected):
    method, path, body = REQUESTS[request_name]
    if body == NEW_BODY:
        body = unique_student()
    elif body == GRADE_BODY:
        body = {"student_id": new_id, "course": "Python", "score": 80}
    with client_for(base_url, token) as client:
        response = client.request(method, path.format(new=new_id), json=body)
    assert response.status_code == expected


# ------------------------------------------- власні дані студента і порядок перевірок

OWN = [
    pytest.param(STUDENT_1, "GET", "/api/students/1", 200, id="student-1-own-card"),
    pytest.param(
        STUDENT_1, "GET", "/api/students/1/grades", 200, id="student-1-own-grades"
    ),
    pytest.param(STUDENT_1, "GET", "/api/students/2", 403, id="student-1-card-of-2"),
    pytest.param(
        STUDENT_1, "GET", "/api/students/2/grades", 403, id="student-1-grades-of-2"
    ),
    pytest.param(
        STUDENT_1, "GET", "/api/students/99999", 403, id="student-1-missing-403"
    ),
    pytest.param(
        STUDENT_1,
        "GET",
        "/api/students/99999/grades",
        403,
        id="student-1-missing-grades-403",
    ),
    pytest.param(STUDENT_1, "PUT", "/api/students/1", 403, id="student-1-updates-self"),
    pytest.param(
        "student-2-token", "GET", "/api/students/2", 200, id="student-2-own-card"
    ),
    pytest.param(
        "student-2-token", "GET", "/api/students/1", 403, id="student-2-card-of-1"
    ),
    pytest.param(TEACHER, "GET", "/api/students/99999", 404, id="teacher-missing-404"),
    pytest.param(
        ADMIN, "GET", "/api/students/99999/grades", 404, id="admin-missing-grades-404"
    ),
    pytest.param(None, "GET", "/api/students/99999", 401, id="no-token-missing-401"),
]


@pytest.mark.parametrize(("token", "method", "path", "expected"), OWN)
def test_own_data_and_check_order(base_url, token, method, path, expected):
    body = unique_student() if method == "PUT" else None
    with client_for(base_url, token) as client:
        response = client.request(method, path, json=body)
    assert response.status_code == expected
