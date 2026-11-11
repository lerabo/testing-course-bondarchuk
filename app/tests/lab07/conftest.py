"""Спільні фікстури тестів ЛР 7: сервер API на вільному порту і клієнти ролей."""

import shutil
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from api_schemas import unique_student

from student_portal.api import create_app
from student_portal.storage import load_group

DATA = Path(__file__).resolve().parents[2] / "data" / "group.json"


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


def client_for(base_url: str, token: str | None) -> httpx.Client:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.Client(base_url=base_url, headers=headers, timeout=5)


@pytest.fixture
def admin(base_url):
    with client_for(base_url, "admin-token") as client:
        yield client


@pytest.fixture
def teacher(base_url):
    with client_for(base_url, "teacher-token") as client:
        yield client


@pytest.fixture
def anonymous(base_url):
    with client_for(base_url, None) as client:
        yield client


@pytest.fixture
def new_student():
    """Дані нового студента з унікальним email."""
    return unique_student()


@pytest.fixture
def created(admin, new_student):
    """Студент, створений адміністратором: (адреса з Location, тіло відповіді)."""
    response = admin.post("/api/students", json=new_student)
    assert response.status_code == 201
    return response.headers["Location"], response.json()
