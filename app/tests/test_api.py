"""REST API (вимога Р-23): основні сценарії."""

import pytest
from fastapi.testclient import TestClient

from student_portal.api import create_app
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


@pytest.fixture
def client():
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95)], email="o@ex.edu"))
    group.add(Student(2, "Андрій", "Мельник", email="a@ex.edu"))
    return TestClient(create_app(group))


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_teacher_lists_students(client):
    response = client.get("/api/students", headers=auth("teacher-token"))

    assert response.status_code == 200
    assert [s["last_name"] for s in response.json()] == ["Коваль", "Мельник"]
    assert response.json()[0]["average"] == 95


def test_request_without_token_is_401(client):
    assert client.get("/api/students").status_code == 401


def test_admin_creates_student(client):
    data = {"first_name": "Тарас", "last_name": "Гнатюк", "email": "t@ex.edu"}

    response = client.post("/api/students", json=data, headers=auth("admin-token"))

    assert response.status_code == 201
    assert response.headers["Location"] == "/api/students/3"
    assert response.json() | data == response.json()


def test_student_sees_own_data(client):
    response = client.get("/api/students/1", headers=auth("student-1-token"))

    assert response.status_code == 200
    assert response.json()["email"] == "o@ex.edu"


def test_teacher_adds_grade(client):
    grade = {"student_id": 2, "course": "Git", "score": 85}

    response = client.post("/api/grades", json=grade, headers=auth("teacher-token"))

    assert response.status_code == 201
    assert response.json()["ects"] == "B"
