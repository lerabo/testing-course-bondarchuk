"""Клієнт сервісу деканату (вимога Р-24): картка студента з REST API."""

from dataclasses import dataclass

import httpx

from student_portal.people import Funding


@dataclass(frozen=True)
class StudentCard:
    full_name: str
    email: str
    group: str
    average: str
    budget: bool


def fetch_student_card(base_url: str, token: str, student_id: int) -> StudentCard:
    response = httpx.get(
        f"{base_url}/api/students/{student_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    return StudentCard(
        full_name=f"{data['last_name']} {data['first_name']}",
        email=data["email"],
        group=data["group"],
        average=f"{data['average']:.1f}",
        budget=data["funding"] == Funding.BUDGET,
    )
