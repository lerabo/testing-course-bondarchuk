"""Фікстури ЛР 10: сервер API на вільному порту (як у ЛР 8)."""

import shutil
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

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
