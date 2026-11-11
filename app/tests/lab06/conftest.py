"""Фікстури ЛР 6: один контейнер PostgreSQL на запуск, одна транзакція на тест."""

import psycopg
import pytest

from student_portal.repository import StudentRepository


@pytest.fixture(scope="session")
def database_url():
    docker = pytest.importorskip("docker")
    from testcontainers.community.postgres import PostgresContainer

    try:
        container = PostgresContainer("postgres:18-alpine", driver=None).start()
    except docker.errors.DockerException as error:
        pytest.skip(f"Docker недоступний: {error}")
    yield container.get_connection_url()
    container.stop()


@pytest.fixture
def repository(database_url):
    with (
        psycopg.connect(database_url) as connection,
        connection.transaction(force_rollback=True),
    ):
        repository = StudentRepository(connection)
        repository.create_schema()
        yield repository
