"""Вебінтерфейс (вимога Р-25): сторінка, статичні файли, роль користувача."""

import pytest
from fastapi.testclient import TestClient

from student_portal.api import create_app
from student_portal.group import Group


@pytest.fixture
def client():
    return TestClient(create_app(Group("КН-11")))


def test_index_page_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "<title>Система управління студентами</title>" in response.text


def test_script_is_served(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


@pytest.mark.parametrize(
    ("token", "me"),
    [
        ("admin-token", {"role": "admin", "student_id": None}),
        ("teacher-token", {"role": "teacher", "student_id": None}),
        ("student-2-token", {"role": "student", "student_id": 2}),
    ],
)
def test_me_returns_role(client, token, me):
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert response.json() == me


def test_me_without_token_is_401(client):
    assert client.get("/api/me").status_code == 401
