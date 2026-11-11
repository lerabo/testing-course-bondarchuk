"""Клієнт сервісу деканату (вимога Р-24)."""

import httpx

from student_portal.dean_client import StudentCard, fetch_student_card


def test_card_from_api_response(monkeypatch):
    body = {
        "id": 1,
        "first_name": "Олена",
        "last_name": "Коваль",
        "email": "o.koval@students.example.edu",
        "group": "КН-11",
        "average": 92.5,
        "funding": "державне замовлення",
    }

    def fake_get(url, headers, timeout):
        assert url == "http://portal/api/students/1"
        assert headers == {"Authorization": "Bearer admin-token"}
        return httpx.Response(200, json=body, request=httpx.Request("GET", url))

    monkeypatch.setattr("student_portal.dean_client.httpx.get", fake_get)

    card = fetch_student_card("http://portal", "admin-token", 1)

    assert card == StudentCard(
        "Коваль Олена", "o.koval@students.example.edu", "КН-11", "92.5", True
    )
