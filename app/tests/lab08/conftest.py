"""Фікстури ЛР 8: сервер API, унікальний email, вхід для ролей, студент через API."""

import itertools
import shutil
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

from student_portal.api import create_app
from student_portal.storage import load_group

from .pages.login_page import LoginPage
from .pages.students_page import StudentsPage

DATA = Path(__file__).resolve().parents[2] / "data" / "group.json"
_counter = itertools.count(1)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    """Запускає API на копії data/group.json; сервер спільний для всіх тестів."""
    data = tmp_path_factory.mktemp("data") / "group.json"
    shutil.copy(DATA, data)
    port = free_port()
    server = uvicorn.Server(
        uvicorn.Config(create_app(load_group(data)), port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join()


@pytest.fixture
def unique_email():
    return f"e2e{next(_counter)}@students.example.edu"


@pytest.fixture
def api(base_url):
    """Клієнт API адміністратора: готує дані для тестів без кліків у браузері."""
    with httpx.Client(
        base_url=base_url, headers={"Authorization": "Bearer admin-token"}, timeout=5
    ) as client:
        yield client


@pytest.fixture
def new_student(api, unique_email):
    """Студент, створений через API: (id, «Прізвище Ім'я»)."""
    n = next(_counter)
    last_name = f"Тестовий{n}"
    body = {"first_name": "Студент", "last_name": last_name, "email": unique_email}
    response = api.post("/api/students", json=body)
    assert response.status_code == 201
    return response.json()["id"], f"{last_name} Студент"


def login_as(page, base_url, token) -> StudentsPage:
    LoginPage(page, base_url).open().login(token)
    return StudentsPage(page).wait_loaded()


@pytest.fixture
def as_admin(page, base_url):
    return login_as(page, base_url, "admin-token")


@pytest.fixture
def as_teacher(page, base_url):
    return login_as(page, base_url, "teacher-token")
